"""
Tests for utility modules.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_importer import CSVImporter
from utils.validators import (
    validate_agent_config, validate_negotiation_setup, 
    analyze_agent_compatibility, get_validation_summary
)
from utils.config_manager import ConfigManager
from models.tactics import TacticLibrary, TacticAspect, TacticType


class TestCSVImporter:
    """Test CSV import functionality."""
    
    def test_import_tactics_from_csv(self, sample_csv_file):
        """Test importing tactics from a valid CSV file."""
        library = CSVImporter.import_tactics_from_csv(sample_csv_file)
        
        assert isinstance(library, TacticLibrary)
        assert len(library.tactics) == 10  # 5 aspects × 2 types each
        
        # Check that all aspects are represented
        aspects = {tactic.aspect for tactic in library.tactics}
        assert len(aspects) == 5
        
        # Check that both tactic types are represented
        types = {tactic.tactic_type for tactic in library.tactics}
        assert TacticType.INFLUENCING in types
        assert TacticType.NEGOTIATION in types
    
    def test_import_nonexistent_file(self, temp_dir):
        """Test importing from a non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError):
            CSVImporter.import_tactics_from_csv(nonexistent_file)
    
    def test_import_invalid_csv_format(self, temp_dir):
        """Test importing from an invalid CSV format."""
        invalid_csv = temp_dir / "invalid.csv"
        with open(invalid_csv, 'w') as f:
            f.write("Wrong,Headers,Here\nData,More,Data")
        
        with pytest.raises(ValueError, match="CSV must contain columns"):
            CSVImporter.import_tactics_from_csv(invalid_csv)
    
    def test_export_tactics_to_csv(self, sample_tactic_library, temp_dir):
        """Test exporting tactics to CSV."""
        export_path = temp_dir / "exported_tactics.csv"
        
        CSVImporter.export_tactics_to_csv(sample_tactic_library, export_path)
        
        assert export_path.exists()
        
        # Verify the exported content can be imported back
        imported_library = CSVImporter.import_tactics_from_csv(export_path)
        assert len(imported_library.tactics) > 0
    
    def test_validate_csv_format_valid(self, sample_csv_file):
        """Test CSV format validation with valid file."""
        result = CSVImporter.validate_csv_format(sample_csv_file)
        
        assert result['is_valid']
        assert len(result['errors']) == 0
        assert result['row_count'] == 5
        assert result['tactic_count'] == 10
    
    def test_validate_csv_format_invalid(self, temp_dir):
        """Test CSV format validation with invalid file."""
        invalid_csv = temp_dir / "invalid.csv"
        with open(invalid_csv, 'w') as f:
            f.write("Wrong,Headers\nData,Data")
        
        result = CSVImporter.validate_csv_format(invalid_csv)
        
        assert not result['is_valid']
        assert len(result['errors']) > 0
    
    def test_create_tactic_from_csv_data(self):
        """Test tactic creation from CSV data."""
        tactic = CSVImporter._create_tactic(
            aspect=TacticAspect.FOCUS,
            name="Test Tactic",
            tactic_type=TacticType.INFLUENCING,
            row_idx=2
        )
        
        assert tactic.name == "Test Tactic"
        assert tactic.aspect == TacticAspect.FOCUS
        assert tactic.tactic_type == TacticType.INFLUENCING
        assert tactic.id == "inf_focus_2"
        assert len(tactic.prompt_modifier) > 0
        assert 0.0 <= tactic.risk_level <= 1.0
        assert tactic.effectiveness_weight > 0.0


class TestValidators:
    """Test validation functions."""
    
    def test_validate_agent_config_valid(self, sample_agent_1, sample_tactic_library):
        """Test validation of a valid agent configuration."""
        result = validate_agent_config(sample_agent_1, sample_tactic_library)
        
        assert result['is_valid']
        assert len(result['errors']) == 0
        assert result['completeness_score'] > 0.8
    
    def test_validate_agent_config_invalid_name(self, sample_personality_1, sample_power_level_1):
        """Test validation with invalid agent name."""
        from models.agent import AgentConfig
        
        with pytest.raises(Exception):  # Should fail during model creation
            AgentConfig(
                name="",  # Invalid empty name
                personality=sample_personality_1,
                power_level=sample_power_level_1,
                zopa_boundaries={}
            )
    
    def test_validate_agent_config_missing_tactics(self, sample_agent_1, sample_tactic_library):
        """Test validation with missing tactics."""
        # Modify agent to have invalid tactic IDs
        sample_agent_1.selected_tactics = ["nonexistent_tactic"]
        
        result = validate_agent_config(sample_agent_1, sample_tactic_library)
        
        assert not result['is_valid']
        assert any("Invalid tactic IDs" in error for error in result['errors'])
    
    def test_validate_agent_config_no_tactics(self, sample_agent_1):
        """Test validation with no tactics selected."""
        sample_agent_1.selected_tactics = []
        
        result = validate_agent_config(sample_agent_1)
        
        assert result['is_valid']  # Still valid, but with warnings
        assert any("No tactics selected" in warning for warning in result['warnings'])
    
    def test_validate_negotiation_setup_valid(self, sample_agent_1, sample_agent_2):
        """Test validation of valid negotiation setup."""
        result = validate_negotiation_setup(sample_agent_1, sample_agent_2, max_rounds=20)
        
        assert result['is_valid']
        assert len(result['errors']) == 0
        assert 'compatibility_analysis' in result
    
    def test_validate_negotiation_setup_invalid_rounds(self, sample_agent_1, sample_agent_2):
        """Test validation with invalid max rounds."""
        result = validate_negotiation_setup(sample_agent_1, sample_agent_2, max_rounds=0)
        
        assert not result['is_valid']
        assert any("max_rounds must be between 1 and 100" in error for error in result['errors'])
    
    def test_analyze_agent_compatibility_good_overlap(self, sample_agent_1, sample_agent_2):
        """Test compatibility analysis with good ZOPA overlap."""
        analysis = analyze_agent_compatibility(sample_agent_1, sample_agent_2)
        
        assert analysis['zopa_overlap_count'] > 0
        assert analysis['negotiation_viability'] in ['high', 'medium', 'low', 'very_low']
        assert 0.0 <= analysis['personality_conflict_risk'] <= 1.0
        assert 0.0 <= analysis['power_imbalance'] <= 1.0
    
    def test_analyze_agent_compatibility_no_overlap(self, sample_agent_1, sample_agent_2):
        """Test compatibility analysis with no ZOPA overlap."""
        # Modify ZOPA boundaries to have no overlap
        sample_agent_1.zopa_boundaries = {
            "volume": {"min_acceptable": 1000, "max_desired": 2000},
            "price": {"min_acceptable": 20.0, "max_desired": 25.0}
        }
        sample_agent_2.zopa_boundaries = {
            "volume": {"min_acceptable": 5000, "max_desired": 8000},
            "price": {"min_acceptable": 5.0, "max_desired": 10.0}
        }
        
        analysis = analyze_agent_compatibility(sample_agent_1, sample_agent_2)
        
        assert analysis['zopa_overlap_count'] == 0
        assert analysis['negotiation_viability'] == 'very_low'
    
    def test_get_validation_summary_success(self):
        """Test validation summary for successful validation."""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': ['Minor warning'],
            'completeness_score': 0.85
        }
        
        summary = get_validation_summary(result)
        
        assert "✅ Validation passed" in summary
        assert "Completeness: 85.0%" in summary
        assert "1 warnings" in summary
    
    def test_get_validation_summary_failure(self):
        """Test validation summary for failed validation."""
        result = {
            'is_valid': False,
            'errors': ['Error 1', 'Error 2'],
            'warnings': ['Warning 1']
        }
        
        summary = get_validation_summary(result)
        
        assert "❌ Validation failed" in summary
        assert "2 errors" in summary
        assert "1 warnings" in summary


class TestConfigManager:
    """Test configuration management."""
    
    def test_config_manager_initialization(self, temp_dir):
        """Test ConfigManager initialization."""
        config_manager = ConfigManager(temp_dir)
        
        assert config_manager.base_path == temp_dir
        assert config_manager.agents_path.exists()
        assert config_manager.negotiations_path.exists()
        assert config_manager.tactics_path.exists()
    
    def test_save_and_load_agent_config(self, config_manager, sample_agent_1):
        """Test saving and loading agent configuration."""
        # Save agent config
        saved_path = config_manager.save_agent_config(sample_agent_1)
        assert saved_path.exists()
        
        # Load agent config
        loaded_agent = config_manager.load_agent_config(sample_agent_1.id)
        assert loaded_agent is not None
        assert loaded_agent.name == sample_agent_1.name
        assert loaded_agent.id == sample_agent_1.id
    
    def test_load_nonexistent_agent_config(self, config_manager):
        """Test loading non-existent agent configuration."""
        loaded_agent = config_manager.load_agent_config("nonexistent_id")
        assert loaded_agent is None
    
    def test_list_agent_configs(self, config_manager, sample_agent_1, sample_agent_2):
        """Test listing agent configurations."""
        # Save multiple agents
        config_manager.save_agent_config(sample_agent_1)
        config_manager.save_agent_config(sample_agent_2)
        
        # List agents
        agent_list = config_manager.list_agent_configs()
        
        assert len(agent_list) == 2
        agent_ids = {agent['id'] for agent in agent_list}
        assert sample_agent_1.id in agent_ids
        assert sample_agent_2.id in agent_ids
    
    def test_delete_agent_config(self, config_manager, sample_agent_1):
        """Test deleting agent configuration."""
        # Save agent
        config_manager.save_agent_config(sample_agent_1)
        
        # Verify it exists
        loaded_agent = config_manager.load_agent_config(sample_agent_1.id)
        assert loaded_agent is not None
        
        # Delete agent
        success = config_manager.delete_agent_config(sample_agent_1.id)
        assert success
        
        # Verify it's gone
        loaded_agent = config_manager.load_agent_config(sample_agent_1.id)
        assert loaded_agent is None
    
    def test_save_and_load_tactic_library(self, config_manager, sample_tactic_library):
        """Test saving and loading tactic library."""
        # Save library
        saved_path = config_manager.save_tactic_library(sample_tactic_library, "test_library")
        assert saved_path.exists()
        
        # Load library
        loaded_library = config_manager.load_tactic_library("test_library")
        assert loaded_library is not None
        assert len(loaded_library.tactics) == len(sample_tactic_library.tactics)
    
    def test_save_and_load_negotiation_state(self, config_manager, sample_negotiation):
        """Test saving and loading negotiation state."""
        # Save negotiation
        saved_path = config_manager.save_negotiation_state(sample_negotiation)
        assert saved_path.exists()
        
        # Load negotiation
        loaded_negotiation = config_manager.load_negotiation_state(sample_negotiation.id)
        assert loaded_negotiation is not None
        assert loaded_negotiation.id == sample_negotiation.id
        assert loaded_negotiation.max_rounds == sample_negotiation.max_rounds
    
    def test_list_negotiations(self, config_manager, sample_negotiation):
        """Test listing negotiations."""
        # Save negotiation
        config_manager.save_negotiation_state(sample_negotiation)
        
        # List negotiations
        negotiation_list = config_manager.list_negotiations()
        
        assert len(negotiation_list) >= 1
        negotiation_ids = {neg['id'] for neg in negotiation_list}
        assert sample_negotiation.id in negotiation_ids
    
    def test_export_agent_config(self, config_manager, sample_agent_1, temp_dir):
        """Test exporting agent configuration."""
        # Save agent
        config_manager.save_agent_config(sample_agent_1)
        
        # Export agent
        export_path = temp_dir / "exported_agent.json"
        success = config_manager.export_agent_config(sample_agent_1.id, export_path)
        
        assert success
        assert export_path.exists()
    
    def test_import_agent_config(self, config_manager, sample_agent_1, temp_dir):
        """Test importing agent configuration."""
        # Create export file
        export_path = temp_dir / "agent_to_import.json"
        config_manager.save_agent_config(sample_agent_1)
        config_manager.export_agent_config(sample_agent_1.id, export_path)
        
        # Import agent (this creates a new agent with new ID)
        imported_agent = config_manager.import_agent_config(export_path)
        
        assert imported_agent is not None
        assert imported_agent.name == sample_agent_1.name
        # ID should be different (new agent)
        assert imported_agent.id != sample_agent_1.id
    
    def test_backup_all_configs(self, config_manager, sample_agent_1, sample_tactic_library, temp_dir):
        """Test creating backup of all configurations."""
        # Save some data
        config_manager.save_agent_config(sample_agent_1)
        config_manager.save_tactic_library(sample_tactic_library, "test")
        
        # Create backup
        backup_path = temp_dir / "backup.json"
        success = config_manager.backup_all_configs(backup_path)
        
        assert success
        assert backup_path.exists()
        
        # Verify backup content
        import json
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        assert 'agents' in backup_data
        assert 'tactic_libraries' in backup_data
        assert len(backup_data['agents']) >= 1
        assert len(backup_data['tactic_libraries']) >= 1
    
    def test_get_storage_stats(self, config_manager, sample_agent_1, sample_tactic_library):
        """Test getting storage statistics."""
        # Save some data
        config_manager.save_agent_config(sample_agent_1)
        config_manager.save_tactic_library(sample_tactic_library, "test")
        
        # Get stats
        stats = config_manager.get_storage_stats()
        
        assert 'agents' in stats
        assert 'tactic_libraries' in stats
        assert 'negotiations' in stats
        assert 'storage_size_mb' in stats
        
        assert stats['agents']['count'] >= 1
        assert stats['tactic_libraries']['count'] >= 1
        assert stats['storage_size_mb'] >= 0.0
