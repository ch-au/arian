"""
Configuration Management Utilities

This module provides utilities for managing agent configurations and negotiation settings.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from datetime import datetime

from ..models.agent import AgentConfig
from ..models.tactics import TacticLibrary
from ..models.negotiation import NegotiationState

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration persistence and loading for the negotiation POC."""
    
    def __init__(self, base_path: Path):
        """
        Initialize the configuration manager.
        
        Args:
            base_path: Base directory for storing configuration files
        """
        self.base_path = Path(base_path)
        self.agents_path = self.base_path / "agents"
        self.negotiations_path = self.base_path / "negotiations"
        self.tactics_path = self.base_path / "tactics"
        
        # Create directories if they don't exist
        for path in [self.agents_path, self.negotiations_path, self.tactics_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def save_agent_config(self, agent_config: AgentConfig) -> Path:
        """
        Save an agent configuration to a JSON file.
        
        Args:
            agent_config: The agent configuration to save
            
        Returns:
            Path to the saved file
        """
        filename = f"agent_{agent_config.id}.json"
        file_path = self.agents_path / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(agent_config.dict(), file, indent=2, default=str)
            
            logger.info(f"Saved agent configuration: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save agent configuration: {e}")
            raise
    
    def load_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Load an agent configuration from a JSON file.
        
        Args:
            agent_id: ID of the agent to load
            
        Returns:
            AgentConfig if found, None otherwise
        """
        filename = f"agent_{agent_id}.json"
        file_path = self.agents_path / filename
        
        if not file_path.exists():
            logger.warning(f"Agent configuration not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            agent_config = AgentConfig(**data)
            logger.info(f"Loaded agent configuration: {agent_config.name}")
            return agent_config
            
        except Exception as e:
            logger.error(f"Failed to load agent configuration: {e}")
            return None
    
    def list_agent_configs(self) -> List[Dict[str, Any]]:
        """
        List all available agent configurations.
        
        Returns:
            List of agent configuration summaries
        """
        configs = []
        
        for file_path in self.agents_path.glob("agent_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Extract summary information
                summary = {
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'created_at': data.get('created_at'),
                    'file_path': str(file_path),
                    'is_fully_configured': data.get('selected_tactics') and data.get('zopa_boundaries')
                }
                configs.append(summary)
                
            except Exception as e:
                logger.warning(f"Failed to read agent config {file_path}: {e}")
                continue
        
        # Sort by creation date (newest first)
        configs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return configs
    
    def delete_agent_config(self, agent_id: str) -> bool:
        """
        Delete an agent configuration file.
        
        Args:
            agent_id: ID of the agent to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        filename = f"agent_{agent_id}.json"
        file_path = self.agents_path / filename
        
        if not file_path.exists():
            logger.warning(f"Agent configuration not found for deletion: {file_path}")
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted agent configuration: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent configuration: {e}")
            return False
    
    def save_tactic_library(self, library: TacticLibrary, name: str = "default") -> Path:
        """
        Save a tactic library to a JSON file.
        
        Args:
            library: The tactic library to save
            name: Name for the library file
            
        Returns:
            Path to the saved file
        """
        filename = f"tactics_{name}.json"
        file_path = self.tactics_path / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(library.dict(), file, indent=2, default=str)
            
            logger.info(f"Saved tactic library: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save tactic library: {e}")
            raise
    
    def load_tactic_library(self, name: str = "default") -> Optional[TacticLibrary]:
        """
        Load a tactic library from a JSON file.
        
        Args:
            name: Name of the library file to load
            
        Returns:
            TacticLibrary if found, None otherwise
        """
        filename = f"tactics_{name}.json"
        file_path = self.tactics_path / filename
        
        if not file_path.exists():
            logger.warning(f"Tactic library not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            library = TacticLibrary(**data)
            logger.info(f"Loaded tactic library with {len(library.tactics)} tactics")
            return library
            
        except Exception as e:
            logger.error(f"Failed to load tactic library: {e}")
            return None
    
    def list_tactic_libraries(self) -> List[Dict[str, Any]]:
        """
        List all available tactic libraries.
        
        Returns:
            List of tactic library summaries
        """
        libraries = []
        
        for file_path in self.tactics_path.glob("tactics_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Extract name from filename
                name = file_path.stem.replace('tactics_', '')
                
                summary = {
                    'name': name,
                    'description': data.get('description'),
                    'version': data.get('version'),
                    'tactic_count': len(data.get('tactics', [])),
                    'file_path': str(file_path)
                }
                libraries.append(summary)
                
            except Exception as e:
                logger.warning(f"Failed to read tactic library {file_path}: {e}")
                continue
        
        return libraries
    
    def save_negotiation_state(self, negotiation: NegotiationState) -> Path:
        """
        Save a negotiation state to a JSON file.
        
        Args:
            negotiation: The negotiation state to save
            
        Returns:
            Path to the saved file
        """
        filename = f"negotiation_{negotiation.id}.json"
        file_path = self.negotiations_path / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(negotiation.dict(), file, indent=2, default=str)
            
            logger.info(f"Saved negotiation state: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save negotiation state: {e}")
            raise
    
    def load_negotiation_state(self, negotiation_id: str) -> Optional[NegotiationState]:
        """
        Load a negotiation state from a JSON file.
        
        Args:
            negotiation_id: ID of the negotiation to load
            
        Returns:
            NegotiationState if found, None otherwise
        """
        filename = f"negotiation_{negotiation_id}.json"
        file_path = self.negotiations_path / filename
        
        if not file_path.exists():
            logger.warning(f"Negotiation state not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            negotiation = NegotiationState(**data)
            logger.info(f"Loaded negotiation state: {negotiation.id}")
            return negotiation
            
        except Exception as e:
            logger.error(f"Failed to load negotiation state: {e}")
            return None
    
    def list_negotiations(self) -> List[Dict[str, Any]]:
        """
        List all available negotiation states.
        
        Returns:
            List of negotiation summaries
        """
        negotiations = []
        
        for file_path in self.negotiations_path.glob("negotiation_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                summary = {
                    'id': data.get('id'),
                    'status': data.get('status'),
                    'agent1_id': data.get('agent1_id'),
                    'agent2_id': data.get('agent2_id'),
                    'current_round': data.get('current_round'),
                    'max_rounds': data.get('max_rounds'),
                    'started_at': data.get('started_at'),
                    'ended_at': data.get('ended_at'),
                    'file_path': str(file_path)
                }
                negotiations.append(summary)
                
            except Exception as e:
                logger.warning(f"Failed to read negotiation {file_path}: {e}")
                continue
        
        # Sort by start date (newest first)
        negotiations.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        return negotiations
    
    def export_agent_config(self, agent_id: str, export_path: Path) -> bool:
        """
        Export an agent configuration to a specified path.
        
        Args:
            agent_id: ID of the agent to export
            export_path: Path where to save the exported configuration
            
        Returns:
            True if exported successfully, False otherwise
        """
        agent_config = self.load_agent_config(agent_id)
        if not agent_config:
            return False
        
        try:
            with open(export_path, 'w', encoding='utf-8') as file:
                json.dump(agent_config.dict(), file, indent=2, default=str)
            
            logger.info(f"Exported agent configuration to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export agent configuration: {e}")
            return False
    
    def import_agent_config(self, import_path: Path) -> Optional[AgentConfig]:
        """
        Import an agent configuration from a specified path.
        
        Args:
            import_path: Path to the configuration file to import
            
        Returns:
            AgentConfig if imported successfully, None otherwise
        """
        if not import_path.exists():
            logger.error(f"Import file not found: {import_path}")
            return None
        
        try:
            with open(import_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Create new agent config (this will generate a new ID)
            agent_config = AgentConfig(**data)
            
            # Save the imported configuration
            self.save_agent_config(agent_config)
            
            logger.info(f"Imported agent configuration: {agent_config.name}")
            return agent_config
            
        except Exception as e:
            logger.error(f"Failed to import agent configuration: {e}")
            return None
    
    def backup_all_configs(self, backup_path: Path) -> bool:
        """
        Create a backup of all configurations.
        
        Args:
            backup_path: Path where to save the backup
            
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            backup_data = {
                'created_at': datetime.now().isoformat(),
                'agents': [],
                'tactic_libraries': [],
                'negotiations': []
            }
            
            # Backup agent configurations
            for agent_summary in self.list_agent_configs():
                agent_config = self.load_agent_config(agent_summary['id'])
                if agent_config:
                    backup_data['agents'].append(agent_config.dict())
            
            # Backup tactic libraries
            for library_summary in self.list_tactic_libraries():
                library = self.load_tactic_library(library_summary['name'])
                if library:
                    backup_data['tactic_libraries'].append({
                        'name': library_summary['name'],
                        'data': library.dict()
                    })
            
            # Backup recent negotiations (last 10)
            for negotiation_summary in self.list_negotiations()[:10]:
                negotiation = self.load_negotiation_state(negotiation_summary['id'])
                if negotiation:
                    backup_data['negotiations'].append(negotiation.dict())
            
            # Save backup
            with open(backup_path, 'w', encoding='utf-8') as file:
                json.dump(backup_data, file, indent=2, default=str)
            
            logger.info(f"Created backup with {len(backup_data['agents'])} agents, "
                       f"{len(backup_data['tactic_libraries'])} libraries, "
                       f"{len(backup_data['negotiations'])} negotiations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored configurations.
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {
            'agents': {
                'count': len(list(self.agents_path.glob("agent_*.json"))),
                'fully_configured': 0
            },
            'tactic_libraries': {
                'count': len(list(self.tactics_path.glob("tactics_*.json"))),
                'total_tactics': 0
            },
            'negotiations': {
                'count': len(list(self.negotiations_path.glob("negotiation_*.json"))),
                'completed': 0,
                'in_progress': 0
            },
            'storage_size_mb': 0.0
        }
        
        # Calculate storage size
        total_size = 0
        for path in [self.agents_path, self.tactics_path, self.negotiations_path]:
            for file_path in path.rglob("*.json"):
                total_size += file_path.stat().st_size
        
        stats['storage_size_mb'] = total_size / (1024 * 1024)
        
        # Count fully configured agents
        for agent_summary in self.list_agent_configs():
            if agent_summary.get('is_fully_configured'):
                stats['agents']['fully_configured'] += 1
        
        # Count total tactics
        for library_summary in self.list_tactic_libraries():
            stats['tactic_libraries']['total_tactics'] += library_summary.get('tactic_count', 0)
        
        # Count negotiation statuses
        for negotiation_summary in self.list_negotiations():
            status = negotiation_summary.get('status', '')
            if 'completed' in status or 'failed' in status or 'agreement' in status:
                stats['negotiations']['completed'] += 1
            elif 'progress' in status:
                stats['negotiations']['in_progress'] += 1
        
        return stats
