"""
Tests for the negotiation engine components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.negotiation_engine import NegotiationEngine
from engine.turn_manager import TurnManager, TurnValidationResult
from engine.zopa_validator import ZOPAValidator, ZOPAValidationResult
from engine.agreement_detector import AgreementDetector, AgreementQuality
from engine.state_manager import StateManager
from models.negotiation import (
    NegotiationState, NegotiationOffer, NegotiationTurn, TurnType, NegotiationStatus
)


class TestNegotiationEngine:
    """Test the main negotiation engine."""
    
    def test_engine_initialization(self, config_manager):
        """Test engine initialization."""
        engine = NegotiationEngine(config_manager)
        
        assert engine.config_manager == config_manager
        assert engine.turn_manager is not None
        assert engine.zopa_validator is not None
        assert engine.agreement_detector is not None
        assert engine.state_manager is not None
    
    def test_create_negotiation_valid(self, config_manager, sample_agent_1, sample_agent_2):
        """Test creating a valid negotiation."""
        engine = NegotiationEngine(config_manager)
        
        negotiation = engine.create_negotiation(
            sample_agent_1, sample_agent_2, max_rounds=10, auto_save=False
        )
        
        assert negotiation is not None
        assert negotiation.agent1_id == sample_agent_1.id
        assert negotiation.agent2_id == sample_agent_2.id
        assert negotiation.max_rounds == 10
        assert len(negotiation.dimensions) > 0
        assert negotiation.status == NegotiationStatus.SETUP
    
    def test_create_negotiation_invalid_setup(self, config_manager, sample_agent_1):
        """Test creating negotiation with invalid setup."""
        engine = NegotiationEngine(config_manager)
        
        # Create agent with no ZOPA overlap
        invalid_agent = sample_agent_1.copy()
        invalid_agent.zopa_boundaries = {}  # No boundaries
        
        with pytest.raises(ValueError, match="Invalid negotiation setup"):
            engine.create_negotiation(sample_agent_1, invalid_agent, max_rounds=10)
    
    def test_run_negotiation_simple(self, config_manager, sample_agent_1, sample_agent_2, sample_negotiation):
        """Test running a simple negotiation."""
        engine = NegotiationEngine(config_manager)
        
        # Mock agent callback that creates offers
        def mock_agent_callback(agent_id, agent_config, negotiation_state):
            return NegotiationOffer(
                agent_id=agent_id,
                turn_number=len(negotiation_state.turns) + 1,
                volume=3000,
                price=12.0,
                payment_terms=45,
                contract_duration=18,
                message=f"Offer from {agent_id}",
                confidence=0.7
            )
        
        # Limit to 2 rounds to avoid infinite loop
        sample_negotiation.max_rounds = 2
        
        # Run the async method synchronously
        result = asyncio.run(engine.run_negotiation(
            sample_negotiation, sample_agent_1, sample_agent_2, mock_agent_callback
        ))
        
        assert result is not None
        assert result.total_turns > 0
        assert result.status in [
            NegotiationStatus.FAILED_MAX_ROUNDS, 
            NegotiationStatus.AGREEMENT_REACHED,
            NegotiationStatus.FAILED_NO_AGREEMENT
        ]
    
    def test_run_negotiation_with_agreement(self, config_manager, sample_agent_1, sample_agent_2, sample_negotiation):
        """Test negotiation that reaches agreement."""
        engine = NegotiationEngine(config_manager)
        
        # Mock agent callback that creates identical offers (agreement)
        call_count = 0
        def mock_agent_callback(agent_id, agent_config, negotiation_state):
            nonlocal call_count
            call_count += 1
            
            # Both agents make the same offer to reach agreement
            return NegotiationOffer(
                agent_id=agent_id,
                turn_number=call_count,
                volume=3000,
                price=12.0,
                payment_terms=45,
                contract_duration=18,
                message=f"Agreement offer from {agent_id}",
                confidence=0.8
            )
        
        # Run the async method synchronously
        result = asyncio.run(engine.run_negotiation(
            sample_negotiation, sample_agent_1, sample_agent_2, mock_agent_callback
        ))
        
        assert result.agreement_reached
        assert result.status == NegotiationStatus.AGREEMENT_REACHED
        assert result.final_agreement is not None
    
    def test_get_negotiation_analysis(self, config_manager, sample_negotiation, sample_offer_1, sample_offer_2):
        """Test negotiation analysis generation."""
        engine = NegotiationEngine(config_manager)
        
        # Add some offers to the negotiation
        sample_negotiation.offers = [sample_offer_1, sample_offer_2]
        
        analysis = engine.get_negotiation_analysis(sample_negotiation)
        
        assert 'basic_info' in analysis
        assert 'turn_analysis' in analysis
        assert 'offer_analysis' in analysis
        assert 'communication_analysis' in analysis
        
        # Basic info should contain negotiation summary
        assert analysis['basic_info']['id'] == sample_negotiation.id
        
        # Offer analysis should reflect the offers we added
        assert analysis['offer_analysis']['total_offers'] == 2


class TestTurnManager:
    """Test the turn management system."""
    
    def test_turn_manager_initialization(self):
        """Test turn manager initialization."""
        manager = TurnManager()
        assert manager is not None
    
    def test_validate_turn_valid(self, sample_negotiation, sample_offer_1):
        """Test validating a valid turn."""
        manager = TurnManager()
        sample_negotiation.start_negotiation()
        
        result = manager.validate_turn(
            sample_negotiation,
            sample_negotiation.agent1_id,
            TurnType.OFFER,
            sample_offer_1
        )
        
        assert result == TurnValidationResult.VALID
    
    def test_validate_turn_wrong_agent(self, sample_negotiation, sample_offer_2):
        """Test validating turn from wrong agent."""
        manager = TurnManager()
        sample_negotiation.start_negotiation()
        
        # Agent 2 tries to go first (should be agent 1's turn)
        result = manager.validate_turn(
            sample_negotiation,
            sample_negotiation.agent2_id,
            TurnType.OFFER,
            sample_offer_2
        )
        
        assert result == TurnValidationResult.INVALID_AGENT
    
    def test_validate_turn_invalid_state(self, sample_negotiation, sample_offer_1):
        """Test validating turn on negotiation not in progress."""
        manager = TurnManager()
        # Don't start negotiation (should be in SETUP state)
        
        result = manager.validate_turn(
            sample_negotiation,
            sample_negotiation.agent1_id,
            TurnType.OFFER,
            sample_offer_1
        )
        
        assert result == TurnValidationResult.INVALID_STATE
    
    def test_get_next_agent(self, sample_negotiation):
        """Test determining next agent."""
        manager = TurnManager()
        
        # First turn should be agent1
        next_agent = manager.get_next_agent(sample_negotiation)
        assert next_agent == sample_negotiation.agent1_id
        
        # Add a turn from agent1
        turn = NegotiationTurn(
            turn_number=1,
            agent_id=sample_negotiation.agent1_id,
            turn_type=TurnType.OFFER,
            message="First turn"
        )
        sample_negotiation.turns.append(turn)
        
        # Next turn should be agent2
        next_agent = manager.get_next_agent(sample_negotiation)
        assert next_agent == sample_negotiation.agent2_id
    
    def test_get_turn_context(self, sample_negotiation, sample_offer_1):
        """Test getting turn context."""
        manager = TurnManager()
        sample_negotiation.start_negotiation()
        
        # Add an offer
        sample_negotiation.offers.append(sample_offer_1)
        
        context = manager.get_turn_context(sample_negotiation, sample_negotiation.agent1_id)
        
        assert 'current_round' in context
        assert 'max_rounds' in context
        assert 'turn_number' in context
        assert 'is_first_turn' in context
        assert 'opponent_id' in context
        assert 'negotiation_history' in context
        assert 'latest_offers' in context
        assert 'dimension_status' in context
        
        assert context['opponent_id'] == sample_negotiation.agent2_id
    
    def test_calculate_turn_urgency(self, sample_negotiation):
        """Test turn urgency calculation."""
        manager = TurnManager()
        sample_negotiation.start_negotiation()
        
        # Early in negotiation should have low urgency
        sample_negotiation.current_round = 1
        urgency = manager.calculate_turn_urgency(sample_negotiation)
        assert 0.0 <= urgency <= 1.0
        assert urgency < 0.5  # Should be low early on
        
        # Late in negotiation should have high urgency
        sample_negotiation.current_round = sample_negotiation.max_rounds - 1
        urgency_late = manager.calculate_turn_urgency(sample_negotiation)
        assert urgency_late > urgency  # Should be higher
    
    def test_get_turn_recommendations(self, sample_negotiation):
        """Test getting turn recommendations."""
        manager = TurnManager()
        sample_negotiation.start_negotiation()
        
        recommendations = manager.get_turn_recommendations(sample_negotiation, sample_negotiation.agent1_id)
        
        assert 'urgency_level' in recommendations
        assert 'suggested_actions' in recommendations
        assert 'concession_opportunities' in recommendations
        assert 'risk_factors' in recommendations
        
        assert isinstance(recommendations['suggested_actions'], list)
        assert 0.0 <= recommendations['urgency_level'] <= 1.0


class TestZOPAValidator:
    """Test ZOPA validation functionality."""
    
    def test_zopa_validator_initialization(self):
        """Test ZOPA validator initialization."""
        validator = ZOPAValidator()
        assert validator is not None
    
    def test_validate_offer_compliant(self, sample_dimensions, sample_offer_1):
        """Test validating a ZOPA-compliant offer."""
        validator = ZOPAValidator()
        
        compliance = validator.validate_offer(sample_offer_1, sample_dimensions)
        
        assert isinstance(compliance, dict)
        assert len(compliance) == len(sample_dimensions)
        
        # Check that all dimensions are evaluated
        for dimension in sample_dimensions:
            assert dimension.name.value in compliance
    
    def test_validate_offer_detailed(self, sample_dimensions, sample_offer_1):
        """Test detailed ZOPA validation."""
        validator = ZOPAValidator()
        
        result = validator.validate_offer_detailed(sample_offer_1, sample_dimensions)
        
        assert isinstance(result, ZOPAValidationResult)
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'compliance_score')
        assert hasattr(result, 'dimension_analysis')
        
        assert 0.0 <= result.compliance_score <= 1.0
    
    def test_get_zopa_recommendations(self, sample_dimensions, sample_offer_1):
        """Test getting ZOPA recommendations."""
        validator = ZOPAValidator()
        
        recommendations = validator.get_zopa_recommendations(sample_offer_1, sample_dimensions)
        
        assert 'adjustments_needed' in recommendations
        assert 'concession_opportunities' in recommendations
        assert 'strategic_advice' in recommendations
        assert 'risk_assessment' in recommendations
        
        assert recommendations['risk_assessment'] in ['low', 'medium', 'high']
        assert isinstance(recommendations['strategic_advice'], list)
    
    def test_analyze_zopa_evolution(self, sample_negotiation, sample_offer_1, sample_offer_2):
        """Test ZOPA evolution analysis."""
        validator = ZOPAValidator()
        
        # Add offers to negotiation
        sample_negotiation.offers = [sample_offer_1, sample_offer_2]
        
        evolution = validator.analyze_zopa_evolution(sample_negotiation)
        
        assert 'compliance_trend' in evolution
        assert 'violation_patterns' in evolution
        assert 'convergence_analysis' in evolution
        assert 'recommendations' in evolution
        
        assert len(evolution['compliance_trend']) == 2  # Two offers
    
    def test_calculate_zopa_utilization(self, sample_negotiation, sample_offer_1, sample_offer_2):
        """Test ZOPA utilization calculation."""
        validator = ZOPAValidator()
        
        # Add offers to negotiation
        sample_negotiation.offers = [sample_offer_1, sample_offer_2]
        
        utilization = validator.calculate_zopa_utilization(sample_negotiation)
        
        assert isinstance(utilization, dict)
        
        # All utilization scores should be between 0 and 1
        for dimension_name, score in utilization.items():
            assert 0.0 <= score <= 1.0
    
    def test_get_optimal_offer_suggestion(self, sample_dimensions):
        """Test optimal offer suggestion."""
        validator = ZOPAValidator()
        
        suggestions = validator.get_optimal_offer_suggestion("agent1", sample_dimensions)
        
        assert isinstance(suggestions, dict)
        
        # Should have suggestions for all dimensions
        for dimension in sample_dimensions:
            assert dimension.name.value in suggestions
            assert isinstance(suggestions[dimension.name.value], (int, float))


class TestAgreementDetector:
    """Test agreement detection functionality."""
    
    def test_agreement_detector_initialization(self):
        """Test agreement detector initialization."""
        detector = AgreementDetector()
        assert detector is not None
    
    def test_check_for_agreement_positive(self, sample_negotiation, sample_agent_1, sample_agent_2):
        """Test detecting agreement when offers match."""
        detector = AgreementDetector()
        
        # Create identical offers
        offer1 = NegotiationOffer(
            agent_id=sample_agent_1.id,
            turn_number=1,
            volume=3000,
            price=15.0,
            payment_terms=60,
            contract_duration=12,
            message="My offer"
        )
        
        offer2 = NegotiationOffer(
            agent_id=sample_agent_2.id,
            turn_number=2,
            volume=3000,
            price=15.0,
            payment_terms=60,
            contract_duration=12,
            message="I accept"
        )
        
        sample_negotiation.offers = [offer1, offer2]
        
        agreement_reached, details = detector.check_for_agreement(sample_negotiation)
        
        assert agreement_reached
        assert details is not None
        assert 'agreed_terms' in details
        assert 'final_offers' in details
        assert details['agreed_terms']['volume'] == 3000
    
    def test_check_for_agreement_negative(self, sample_negotiation, sample_offer_1, sample_offer_2):
        """Test detecting no agreement when offers differ."""
        detector = AgreementDetector()
        
        sample_negotiation.offers = [sample_offer_1, sample_offer_2]
        
        agreement_reached, details = detector.check_for_agreement(sample_negotiation)
        
        assert not agreement_reached
        assert details is None
    
    def test_check_for_near_agreement(self, sample_negotiation, sample_agent_1, sample_agent_2):
        """Test detecting near agreement."""
        detector = AgreementDetector()
        
        # Create offers that are close but not identical
        offer1 = NegotiationOffer(
            agent_id=sample_agent_1.id,
            turn_number=1,
            volume=3000,
            price=15.0,
            payment_terms=60,
            contract_duration=12,
            message="My offer"
        )
        
        offer2 = NegotiationOffer(
            agent_id=sample_agent_2.id,
            turn_number=2,
            volume=3050,  # Close to 3000
            price=15.2,   # Close to 15.0
            payment_terms=62,  # Close to 60
            contract_duration=12,  # Identical
            message="Counter offer"
        )
        
        sample_negotiation.offers = [offer1, offer2]
        
        near_agreement, analysis = detector.check_for_near_agreement(sample_negotiation, tolerance_percentage=0.05)
        
        assert isinstance(near_agreement, bool)
        assert analysis is not None
        assert 'near_agreement' in analysis
        assert 'tolerance_used' in analysis
        assert 'dimensions_analysis' in analysis
    
    def test_assess_agreement_quality(self, sample_negotiation, sample_agent_1, sample_agent_2):
        """Test agreement quality assessment."""
        detector = AgreementDetector()
        
        # Create agreement details
        agreement_details = {
            'agreed_terms': {
                'volume': 3000,
                'price': 15.0,
                'payment_terms': 60,
                'contract_duration': 12
            },
            'negotiation_rounds': 5,
            'agreement_turn': 10
        }
        
        quality = detector.assess_agreement_quality(sample_negotiation, agreement_details)
        
        assert isinstance(quality, AgreementQuality)
        assert 0.0 <= quality.overall_score <= 1.0
        assert 0.0 <= quality.mutual_satisfaction <= 1.0
        assert 0.0 <= quality.zopa_compliance <= 1.0
        assert 0.0 <= quality.efficiency_score <= 1.0
        assert 0.0 <= quality.fairness_score <= 1.0
        assert 0.0 <= quality.stability_score <= 1.0
    
    def test_generate_agreement_report(self, sample_negotiation, sample_agent_1, sample_agent_2):
        """Test agreement report generation."""
        detector = AgreementDetector()
        
        agreement_details = {
            'agreed_terms': {
                'volume': 3000,
                'price': 15.0,
                'payment_terms': 60,
                'contract_duration': 12
            },
            'negotiation_rounds': 5,
            'agreement_turn': 10
        }
        
        quality = detector.assess_agreement_quality(sample_negotiation, agreement_details)
        report = detector.generate_agreement_report(sample_negotiation, agreement_details, quality)
        
        assert 'negotiation_id' in report
        assert 'agreement_summary' in report
        assert 'quality_assessment' in report
        assert 'detailed_analysis' in report
        assert 'recommendations' in report
        assert 'success_factors' in report
        assert 'lessons_learned' in report
        
        assert report['negotiation_id'] == sample_negotiation.id


class TestStateManager:
    """Test state management functionality."""
    
    def test_state_manager_initialization(self, config_manager):
        """Test state manager initialization."""
        manager = StateManager(config_manager)
        
        assert manager.config_manager == config_manager
        assert hasattr(manager, '_state_cache')
        assert hasattr(manager, '_cache_max_size')
    
    def test_save_and_load_negotiation_state(self, config_manager, sample_negotiation):
        """Test saving and loading negotiation state."""
        manager = StateManager(config_manager)
        
        # Save state
        success = manager.save_negotiation_state(sample_negotiation)
        assert success
        
        # Load state
        loaded_negotiation = manager.load_negotiation_state(sample_negotiation.id)
        assert loaded_negotiation is not None
        assert loaded_negotiation.id == sample_negotiation.id
        assert loaded_negotiation.max_rounds == sample_negotiation.max_rounds
    
    def test_create_checkpoint(self, config_manager, sample_negotiation):
        """Test creating negotiation checkpoint."""
        manager = StateManager(config_manager)
        
        checkpoint_id = manager.create_checkpoint(sample_negotiation, "test_checkpoint")
        
        assert checkpoint_id is not None
        assert "test_checkpoint" in checkpoint_id
        assert sample_negotiation.id in checkpoint_id
    
    def test_restore_from_checkpoint(self, config_manager, sample_negotiation):
        """Test restoring from checkpoint."""
        manager = StateManager(config_manager)
        
        # Create checkpoint
        checkpoint_id = manager.create_checkpoint(sample_negotiation, "restore_test")
        
        # Restore from checkpoint
        restored_negotiation = manager.restore_from_checkpoint(checkpoint_id)
        
        assert restored_negotiation is not None
        assert restored_negotiation.id == sample_negotiation.id
        assert restored_negotiation.max_rounds == sample_negotiation.max_rounds
    
    def test_list_checkpoints(self, config_manager, sample_negotiation):
        """Test listing checkpoints."""
        manager = StateManager(config_manager)
        
        # Create multiple checkpoints
        checkpoint1 = manager.create_checkpoint(sample_negotiation, "checkpoint1")
        checkpoint2 = manager.create_checkpoint(sample_negotiation, "checkpoint2")
        
        # List checkpoints
        checkpoints = manager.list_checkpoints(sample_negotiation.id)
        
        assert len(checkpoints) >= 2
        checkpoint_names = {cp['checkpoint_name'] for cp in checkpoints}
        assert 'checkpoint1' in checkpoint_names
        assert 'checkpoint2' in checkpoint_names
    
    def test_delete_checkpoint(self, config_manager, sample_negotiation):
        """Test deleting checkpoint."""
        manager = StateManager(config_manager)
        
        # Create checkpoint
        checkpoint_id = manager.create_checkpoint(sample_negotiation, "to_delete")
        
        # Verify it exists
        checkpoints = manager.list_checkpoints(sample_negotiation.id)
        assert any(cp['checkpoint_name'] == 'to_delete' for cp in checkpoints)
        
        # Delete checkpoint
        success = manager.delete_checkpoint(checkpoint_id)
        assert success
        
        # Verify it's gone
        checkpoints_after = manager.list_checkpoints(sample_negotiation.id)
        assert not any(cp['checkpoint_name'] == 'to_delete' for cp in checkpoints_after)
    
    def test_get_negotiation_history(self, config_manager, sample_negotiation):
        """Test getting negotiation history."""
        manager = StateManager(config_manager)
        
        # Save negotiation and create checkpoint
        manager.save_negotiation_state(sample_negotiation)
        manager.create_checkpoint(sample_negotiation, "history_test")
        
        history = manager.get_negotiation_history(sample_negotiation.id)
        
        assert 'negotiation_id' in history
        assert 'current_state' in history
        assert 'checkpoints' in history
        assert 'state_changes' in history
        assert 'statistics' in history
        
        assert history['negotiation_id'] == sample_negotiation.id
        assert len(history['checkpoints']) >= 1
    
    def test_validate_state_integrity(self, config_manager, sample_negotiation):
        """Test state integrity validation."""
        manager = StateManager(config_manager)
        
        validation = manager.validate_state_integrity(sample_negotiation)
        
        assert 'is_valid' in validation
        assert 'errors' in validation
        assert 'warnings' in validation
        assert 'statistics' in validation
        
        # Should be valid for our sample negotiation
        assert validation['is_valid']
        assert len(validation['errors']) == 0
    
    def test_export_negotiation_data(self, config_manager, sample_negotiation, temp_dir):
        """Test exporting negotiation data."""
        manager = StateManager(config_manager)
        
        # Save negotiation first
        manager.save_negotiation_state(sample_negotiation)
        
        # Export data
        export_path = temp_dir / "exported_negotiation.json"
        success = manager.export_negotiation_data(sample_negotiation.id, export_path)
        
        assert success
        assert export_path.exists()
        
        # Verify export content
        import json
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        assert 'export_info' in export_data
        assert 'negotiation_state' in export_data
        assert 'history' in export_data
        assert 'validation' in export_data
    
    def test_get_state_summary(self, config_manager, sample_negotiation):
        """Test getting state summary."""
        manager = StateManager(config_manager)
        
        # Save some data
        manager.save_negotiation_state(sample_negotiation)
        
        summary = manager.get_state_summary()
        
        assert 'total_negotiations' in summary
        assert 'active_negotiations' in summary
        assert 'completed_negotiations' in summary
        assert 'failed_negotiations' in summary
        assert 'cache_size' in summary
        assert 'storage_stats' in summary
        assert 'recent_activity' in summary
        
        assert summary['total_negotiations'] >= 1
        assert summary['cache_size'] >= 0
