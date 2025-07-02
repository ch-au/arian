"""
Tests for the core data models.
"""

import pytest
from pydantic import ValidationError
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import (
    NegotiationDimension, DimensionType, NegotiationOffer, NegotiationState,
    NegotiationTurn, TurnType, NegotiationStatus
)
from models.tactics import (
    NegotiationTactic, TacticAspect, TacticType, TacticLibrary
)
from models.zopa import ZOPABoundary, ZOPAOverlap, ZOPAAnalysis


class TestPersonalityProfile:
    """Test PersonalityProfile model."""
    
    def test_valid_personality_creation(self):
        """Test creating a valid personality profile."""
        personality = PersonalityProfile(
            openness=0.7,
            conscientiousness=0.8,
            extraversion=0.6,
            agreeableness=0.5,
            neuroticism=0.3
        )
        
        assert personality.openness == 0.7
        assert personality.conscientiousness == 0.8
        assert personality.extraversion == 0.6
        assert personality.agreeableness == 0.5
        assert personality.neuroticism == 0.3
    
    def test_personality_validation_bounds(self):
        """Test personality trait validation bounds."""
        # Test lower bound
        with pytest.raises(ValidationError):
            PersonalityProfile(
                openness=-0.1,
                conscientiousness=0.5,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.5
            )
        
        # Test upper bound
        with pytest.raises(ValidationError):
            PersonalityProfile(
                openness=1.1,
                conscientiousness=0.5,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.5
            )
    
    def test_personality_summary(self):
        """Test personality summary generation."""
        personality = PersonalityProfile(
            openness=0.8,
            conscientiousness=0.9,
            extraversion=0.3,
            agreeableness=0.7,
            neuroticism=0.2
        )
        
        summary = personality.get_summary()
        assert "High openness" in summary
        assert "High conscientiousness" in summary
        assert "Low extraversion" in summary
        assert "High agreeableness" in summary
        assert "Low neuroticism" in summary


class TestPowerLevel:
    """Test PowerLevel model."""
    
    def test_valid_power_level_creation(self):
        """Test creating a valid power level."""
        power = PowerLevel(
            level=0.7,
            description="Senior Manager",
            sources=["Position", "Expertise"]
        )
        
        assert power.level == 0.7
        assert power.description == "Senior Manager"
        assert "Position" in power.sources
        assert "Expertise" in power.sources
    
    def test_power_level_validation(self):
        """Test power level validation."""
        # Test lower bound
        with pytest.raises(ValidationError):
            PowerLevel(level=-0.1, description="Invalid")
        
        # Test upper bound
        with pytest.raises(ValidationError):
            PowerLevel(level=1.1, description="Invalid")
    
    def test_power_level_category(self):
        """Test power level categorization."""
        low_power = PowerLevel(level=0.2, description="Junior")
        medium_power = PowerLevel(level=0.5, description="Manager")
        high_power = PowerLevel(level=0.8, description="Director")
        
        assert low_power.get_category() == "Low"
        assert medium_power.get_category() == "Medium"
        assert high_power.get_category() == "High"


class TestAgentConfig:
    """Test AgentConfig model."""
    
    def test_valid_agent_creation(self, sample_agent_1):
        """Test creating a valid agent configuration."""
        assert sample_agent_1.name == "Alice"
        assert sample_agent_1.description == "Experienced procurement manager"
        assert len(sample_agent_1.selected_tactics) == 2
        assert len(sample_agent_1.zopa_boundaries) == 4
    
    def test_agent_validation_empty_name(self, sample_personality_1, sample_power_level_1):
        """Test agent validation with empty name."""
        with pytest.raises(ValidationError):
            AgentConfig(
                name="",
                personality=sample_personality_1,
                power_level=sample_power_level_1,
                zopa_boundaries={}
            )
    
    def test_get_zopa_for_dimension(self, sample_agent_1):
        """Test getting ZOPA boundaries for a specific dimension."""
        volume_zopa = sample_agent_1.get_zopa_for_dimension("volume")
        assert volume_zopa is not None
        assert volume_zopa["min_acceptable"] == 1000
        assert volume_zopa["max_desired"] == 5000
        
        # Test non-existent dimension
        invalid_zopa = sample_agent_1.get_zopa_for_dimension("invalid_dimension")
        assert invalid_zopa is None
    
    def test_agent_summary(self, sample_agent_1):
        """Test agent summary generation."""
        summary = sample_agent_1.get_summary()
        assert summary["name"] == "Alice"
        assert summary["personality_summary"] is not None
        assert summary["power_category"] is not None
        assert summary["tactics_count"] == 2
        assert summary["zopa_dimensions"] == 4


class TestNegotiationDimension:
    """Test NegotiationDimension model."""
    
    def test_valid_dimension_creation(self):
        """Test creating a valid negotiation dimension."""
        dimension = NegotiationDimension(
            name=DimensionType.VOLUME,
            unit="units",
            agent1_min=1000,
            agent1_max=5000,
            agent2_min=2000,
            agent2_max=8000
        )
        
        assert dimension.name == DimensionType.VOLUME
        assert dimension.unit == "units"
        assert dimension.agent1_min == 1000
        assert dimension.agent1_max == 5000
    
    def test_dimension_overlap_detection(self):
        """Test ZOPA overlap detection."""
        # Overlapping dimension
        overlapping = NegotiationDimension(
            name=DimensionType.PRICE,
            unit="$/unit",
            agent1_min=10.0,
            agent1_max=20.0,
            agent2_min=15.0,
            agent2_max=25.0
        )
        assert overlapping.has_overlap()
        
        # Non-overlapping dimension
        non_overlapping = NegotiationDimension(
            name=DimensionType.PRICE,
            unit="$/unit",
            agent1_min=10.0,
            agent1_max=15.0,
            agent2_min=20.0,
            agent2_max=25.0
        )
        assert not non_overlapping.has_overlap()
    
    def test_overlap_range_calculation(self):
        """Test overlap range calculation."""
        dimension = NegotiationDimension(
            name=DimensionType.VOLUME,
            unit="units",
            agent1_min=1000,
            agent1_max=5000,
            agent2_min=3000,
            agent2_max=7000
        )
        
        overlap_range = dimension.get_overlap_range()
        assert overlap_range is not None
        assert overlap_range[0] == 3000  # max(1000, 3000)
        assert overlap_range[1] == 5000  # min(5000, 7000)
    
    def test_value_acceptability(self):
        """Test value acceptability checking."""
        dimension = NegotiationDimension(
            name=DimensionType.PRICE,
            unit="$/unit",
            agent1_min=10.0,
            agent1_max=20.0,
            agent2_min=15.0,
            agent2_max=25.0
        )
        
        # Test agent1 acceptability
        assert dimension.is_value_acceptable_to_agent(15.0, "agent1")
        assert not dimension.is_value_acceptable_to_agent(25.0, "agent1")
        
        # Test agent2 acceptability
        assert dimension.is_value_acceptable_to_agent(20.0, "agent2")
        assert not dimension.is_value_acceptable_to_agent(10.0, "agent2")


class TestNegotiationOffer:
    """Test NegotiationOffer model."""
    
    def test_valid_offer_creation(self, sample_offer_1):
        """Test creating a valid negotiation offer."""
        assert sample_offer_1.volume == 3000
        assert sample_offer_1.price == 15.0
        assert sample_offer_1.payment_terms == 60
        assert sample_offer_1.contract_duration == 12
        assert sample_offer_1.confidence == 0.8
    
    def test_offer_validation(self, sample_agent_1):
        """Test offer validation."""
        # Test negative volume
        with pytest.raises(ValidationError):
            NegotiationOffer(
                agent_id=sample_agent_1.id,
                turn_number=1,
                volume=-100,
                price=15.0,
                payment_terms=60,
                contract_duration=12,
                message="Invalid offer"
            )
        
        # Test invalid payment terms
        with pytest.raises(ValidationError):
            NegotiationOffer(
                agent_id=sample_agent_1.id,
                turn_number=1,
                volume=1000,
                price=15.0,
                payment_terms=400,  # > 365 days
                contract_duration=12,
                message="Invalid offer"
            )
    
    def test_offer_to_dict(self, sample_offer_1):
        """Test offer dictionary conversion."""
        offer_dict = sample_offer_1.to_dict()
        assert offer_dict["volume"] == 3000
        assert offer_dict["price"] == 15.0
        assert offer_dict["payment_terms"] == 60
        assert offer_dict["contract_duration"] == 12
    
    def test_total_value_calculation(self, sample_offer_1):
        """Test total value calculation."""
        total_value = sample_offer_1.calculate_total_value()
        assert total_value == 3000 * 15.0  # volume * price


class TestNegotiationState:
    """Test NegotiationState model."""
    
    def test_valid_negotiation_creation(self, sample_negotiation):
        """Test creating a valid negotiation state."""
        assert sample_negotiation.max_rounds == 10
        assert len(sample_negotiation.dimensions) == 4
        assert sample_negotiation.status == NegotiationStatus.SETUP
        assert sample_negotiation.current_round == 0
    
    def test_negotiation_start(self, sample_negotiation):
        """Test starting a negotiation."""
        sample_negotiation.start_negotiation()
        
        assert sample_negotiation.status == NegotiationStatus.IN_PROGRESS
        assert sample_negotiation.current_round == 1
        assert sample_negotiation.started_at is not None
        assert sample_negotiation.current_turn_agent == sample_negotiation.agent1_id
    
    def test_add_turn(self, sample_negotiation, sample_offer_1):
        """Test adding turns to negotiation."""
        sample_negotiation.start_negotiation()
        
        turn = NegotiationTurn(
            turn_number=1,
            agent_id=sample_negotiation.agent1_id,
            turn_type=TurnType.OFFER,
            offer=sample_offer_1,
            message="First offer"
        )
        
        sample_negotiation.add_turn(turn)
        
        assert len(sample_negotiation.turns) == 1
        assert len(sample_negotiation.offers) == 1
        assert sample_negotiation.current_turn_agent == sample_negotiation.agent2_id
    
    def test_agreement_detection(self, sample_negotiation, sample_agent_1, sample_agent_2):
        """Test agreement detection."""
        sample_negotiation.start_negotiation()
        
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
        
        assert sample_negotiation.check_agreement()
    
    def test_termination_conditions(self, sample_negotiation):
        """Test negotiation termination conditions."""
        sample_negotiation.start_negotiation()
        
        # Test max rounds exceeded
        sample_negotiation.current_round = 11  # > max_rounds (10)
        should_terminate, reason = sample_negotiation.should_terminate()
        assert should_terminate
        assert reason == "max_rounds_exceeded"


class TestNegotiationTactic:
    """Test NegotiationTactic model."""
    
    def test_valid_tactic_creation(self, sample_tactics):
        """Test creating valid negotiation tactics."""
        tactic = sample_tactics[0]
        assert tactic.name == "Collaborative Approach"
        assert tactic.aspect == TacticAspect.APPROACH
        assert tactic.tactic_type == TacticType.INFLUENCING
        assert tactic.risk_level == 0.2
        assert tactic.effectiveness_weight == 1.2
    
    def test_tactic_validation(self):
        """Test tactic validation."""
        # Test invalid risk level
        with pytest.raises(ValidationError):
            NegotiationTactic(
                id="invalid",
                name="Invalid Tactic",
                aspect=TacticAspect.APPROACH,
                tactic_type=TacticType.INFLUENCING,
                description="Invalid tactic",
                prompt_modifier="Invalid",
                risk_level=1.5  # > 1.0
            )
    
    def test_personality_compatibility(self, sample_tactics):
        """Test personality compatibility calculation."""
        tactic = sample_tactics[0]  # Collaborative Approach
        
        # High agreeableness should be compatible
        high_agreeableness_personality = PersonalityProfile(
            openness=0.5, conscientiousness=0.5, extraversion=0.5,
            agreeableness=0.9, neuroticism=0.5
        )
        
        compatibility = tactic.calculate_personality_compatibility(high_agreeableness_personality)
        assert compatibility > 0.5  # Should be compatible
        
        # Low agreeableness should be less compatible
        low_agreeableness_personality = PersonalityProfile(
            openness=0.5, conscientiousness=0.5, extraversion=0.5,
            agreeableness=0.1, neuroticism=0.5
        )
        
        compatibility_low = tactic.calculate_personality_compatibility(low_agreeableness_personality)
        assert compatibility_low < compatibility


class TestTacticLibrary:
    """Test TacticLibrary model."""
    
    def test_library_creation(self, sample_tactic_library):
        """Test creating a tactic library."""
        assert len(sample_tactic_library.tactics) == 4
        assert sample_tactic_library.description == "Sample tactics for testing"
    
    def test_add_tactic(self, sample_tactics):
        """Test adding tactics to library."""
        library = TacticLibrary()
        tactic = sample_tactics[0]
        
        library.add_tactic(tactic)
        assert len(library.tactics) == 1
        assert library.get_tactic(tactic.id) == tactic
    
    def test_get_tactics_by_aspect(self, sample_tactic_library):
        """Test filtering tactics by aspect."""
        approach_tactics = sample_tactic_library.get_tactics_by_aspect(TacticAspect.APPROACH)
        assert len(approach_tactics) == 2  # Collaborative Approach and Competitive Positioning
    
    def test_get_tactics_by_type(self, sample_tactic_library):
        """Test filtering tactics by type."""
        influencing_tactics = sample_tactic_library.get_tactics_by_type(TacticType.INFLUENCING)
        assert len(influencing_tactics) == 2  # Collaborative Approach and Building Rapport
    
    def test_get_compatible_tactics(self, sample_tactic_library):
        """Test getting personality-compatible tactics."""
        # High agreeableness personality
        personality = PersonalityProfile(
            openness=0.5, conscientiousness=0.5, extraversion=0.5,
            agreeableness=0.9, neuroticism=0.5
        )
        
        compatible_tactics = sample_tactic_library.get_compatible_tactics(personality, threshold=0.5)
        assert len(compatible_tactics) > 0
        
        # All returned tactics should have compatibility > threshold
        for tactic in compatible_tactics:
            compatibility = tactic.calculate_personality_compatibility(personality)
            assert compatibility > 0.5


class TestZOPABoundary:
    """Test ZOPABoundary model."""
    
    def test_boundary_creation(self):
        """Test creating ZOPA boundaries."""
        boundary = ZOPABoundary(
            agent_id="agent1",
            dimension="volume",
            min_acceptable=1000,
            max_desired=5000
        )
        
        assert boundary.agent_id == "agent1"
        assert boundary.dimension == "volume"
        assert boundary.min_acceptable == 1000
        assert boundary.max_desired == 5000
    
    def test_boundary_validation(self):
        """Test ZOPA boundary validation."""
        # Test max_desired <= min_acceptable
        with pytest.raises(ValidationError):
            ZOPABoundary(
                agent_id="agent1",
                dimension="volume",
                min_acceptable=5000,
                max_desired=1000  # Invalid: max < min
            )
    
    def test_satisfaction_calculation(self):
        """Test satisfaction calculation."""
        boundary = ZOPABoundary(
            agent_id="agent1",
            dimension="price",
            min_acceptable=10.0,
            max_desired=20.0,
            preferred_value=15.0
        )
        
        # Test satisfaction at preferred value
        assert boundary.calculate_satisfaction(15.0) == 1.0
        
        # Test satisfaction at boundaries
        assert boundary.calculate_satisfaction(10.0) < 1.0
        assert boundary.calculate_satisfaction(20.0) < 1.0
        
        # Test satisfaction outside range
        assert boundary.calculate_satisfaction(5.0) == 0.0
        assert boundary.calculate_satisfaction(25.0) == 0.0


class TestZOPAOverlap:
    """Test ZOPAOverlap model."""
    
    def test_overlap_calculation(self):
        """Test ZOPA overlap calculation."""
        boundary1 = ZOPABoundary(
            agent_id="agent1",
            dimension="volume",
            min_acceptable=1000,
            max_desired=5000
        )
        
        boundary2 = ZOPABoundary(
            agent_id="agent2",
            dimension="volume",
            min_acceptable=3000,
            max_desired=7000
        )
        
        overlap = ZOPAOverlap(
            dimension="volume",
            agent1_boundary=boundary1,
            agent2_boundary=boundary2
        )
        
        assert overlap.has_overlap
        assert overlap.overlap_min == 3000
        assert overlap.overlap_max == 5000
        assert overlap.overlap_size == 2000
    
    def test_no_overlap(self):
        """Test case with no ZOPA overlap."""
        boundary1 = ZOPABoundary(
            agent_id="agent1",
            dimension="price",
            min_acceptable=20.0,
            max_desired=25.0
        )
        
        boundary2 = ZOPABoundary(
            agent_id="agent2",
            dimension="price",
            min_acceptable=10.0,
            max_desired=15.0
        )
        
        overlap = ZOPAOverlap(
            dimension="price",
            agent1_boundary=boundary1,
            agent2_boundary=boundary2
        )
        
        assert not overlap.has_overlap
        assert overlap.overlap_min is None
        assert overlap.overlap_max is None
        assert overlap.overlap_size == 0.0
    
    def test_optimal_value_calculation(self):
        """Test optimal value calculation in overlap."""
        boundary1 = ZOPABoundary(
            agent_id="agent1",
            dimension="volume",
            min_acceptable=1000,
            max_desired=5000,
            preferred_value=4000
        )
        
        boundary2 = ZOPABoundary(
            agent_id="agent2",
            dimension="volume",
            min_acceptable=3000,
            max_desired=7000,
            preferred_value=4000
        )
        
        overlap = ZOPAOverlap(
            dimension="volume",
            agent1_boundary=boundary1,
            agent2_boundary=boundary2
        )
        
        optimal_value = overlap.get_optimal_value()
        assert optimal_value is not None
        assert 3000 <= optimal_value <= 5000  # Within overlap range
