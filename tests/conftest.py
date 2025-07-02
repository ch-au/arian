"""
Pytest configuration and shared fixtures for the negotiation POC tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import NegotiationDimension, DimensionType, NegotiationState, NegotiationOffer
from models.tactics import TacticLibrary, NegotiationTactic, TacticAspect, TacticType
from utils.config_manager import ConfigManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_manager(temp_dir):
    """Create a ConfigManager instance with temporary storage."""
    return ConfigManager(temp_dir)


@pytest.fixture
def sample_personality_1():
    """Sample personality profile for agent 1."""
    return PersonalityProfile(
        openness=0.7,
        conscientiousness=0.8,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.3
    )


@pytest.fixture
def sample_personality_2():
    """Sample personality profile for agent 2."""
    return PersonalityProfile(
        openness=0.5,
        conscientiousness=0.6,
        extraversion=0.8,
        agreeableness=0.7,
        neuroticism=0.4
    )


@pytest.fixture
def sample_power_level_1():
    """Sample power level for agent 1."""
    return PowerLevel(
        level=0.7,
        description="Senior Manager",
        sources=["Position", "Expertise", "Network"]
    )


@pytest.fixture
def sample_power_level_2():
    """Sample power level for agent 2."""
    return PowerLevel(
        level=0.5,
        description="Team Lead",
        sources=["Position", "Expertise"]
    )


@pytest.fixture
def sample_zopa_boundaries_1():
    """Sample ZOPA boundaries for agent 1."""
    return {
        "volume": {"min_acceptable": 1000, "max_desired": 5000},
        "price": {"min_acceptable": 10.0, "max_desired": 20.0},
        "payment_terms": {"min_acceptable": 30, "max_desired": 90},
        "contract_duration": {"min_acceptable": 6, "max_desired": 24}
    }


@pytest.fixture
def sample_zopa_boundaries_2():
    """Sample ZOPA boundaries for agent 2."""
    return {
        "volume": {"min_acceptable": 2000, "max_desired": 8000},
        "price": {"min_acceptable": 8.0, "max_desired": 15.0},
        "payment_terms": {"min_acceptable": 15, "max_desired": 60},
        "contract_duration": {"min_acceptable": 12, "max_desired": 36}
    }


@pytest.fixture
def sample_agent_1(sample_personality_1, sample_power_level_1, sample_zopa_boundaries_1):
    """Create a sample agent configuration 1."""
    return AgentConfig(
        name="Alice",
        description="Experienced procurement manager",
        personality=sample_personality_1,
        power_level=sample_power_level_1,
        selected_tactics=["tactic_1", "tactic_2"],
        zopa_boundaries=sample_zopa_boundaries_1
    )


@pytest.fixture
def sample_agent_2(sample_personality_2, sample_power_level_2, sample_zopa_boundaries_2):
    """Create a sample agent configuration 2."""
    return AgentConfig(
        name="Bob",
        description="Sales director with strong negotiation skills",
        personality=sample_personality_2,
        power_level=sample_power_level_2,
        selected_tactics=["tactic_3", "tactic_4"],
        zopa_boundaries=sample_zopa_boundaries_2
    )


@pytest.fixture
def sample_tactics():
    """Create sample negotiation tactics."""
    return [
        NegotiationTactic(
            id="tactic_1",
            name="Collaborative Approach",
            aspect=TacticAspect.APPROACH,
            tactic_type=TacticType.INFLUENCING,
            description="Focus on mutual benefits and win-win solutions",
            prompt_modifier="Use collaborative language and seek mutual benefits",
            personality_affinity={"agreeableness": 0.8, "openness": 0.6},
            risk_level=0.2,
            effectiveness_weight=1.2
        ),
        NegotiationTactic(
            id="tactic_2",
            name="Anchoring",
            aspect=TacticAspect.TIMING,
            tactic_type=TacticType.NEGOTIATION,
            description="Set initial reference point for negotiations",
            prompt_modifier="Make strong opening offers to anchor expectations",
            personality_affinity={"conscientiousness": 0.7, "extraversion": 0.6},
            risk_level=0.5,
            effectiveness_weight=1.1
        ),
        NegotiationTactic(
            id="tactic_3",
            name="Building Rapport",
            aspect=TacticAspect.TONE,
            tactic_type=TacticType.INFLUENCING,
            description="Establish personal connection and trust",
            prompt_modifier="Use warm, personal language to build relationship",
            personality_affinity={"agreeableness": 0.9, "extraversion": 0.7},
            risk_level=0.1,
            effectiveness_weight=1.0
        ),
        NegotiationTactic(
            id="tactic_4",
            name="Competitive Positioning",
            aspect=TacticAspect.APPROACH,
            tactic_type=TacticType.NEGOTIATION,
            description="Emphasize competitive advantages and alternatives",
            prompt_modifier="Highlight your strong position and alternatives",
            personality_affinity={"extraversion": 0.8, "agreeableness": 0.2},
            risk_level=0.7,
            effectiveness_weight=1.3
        )
    ]


@pytest.fixture
def sample_tactic_library(sample_tactics):
    """Create a sample tactic library."""
    library = TacticLibrary(description="Sample tactics for testing")
    for tactic in sample_tactics:
        library.add_tactic(tactic)
    return library


@pytest.fixture
def sample_dimensions():
    """Create sample negotiation dimensions."""
    return [
        NegotiationDimension(
            name=DimensionType.VOLUME,
            unit="units",
            agent1_min=1000,
            agent1_max=5000,
            agent2_min=2000,
            agent2_max=8000
        ),
        NegotiationDimension(
            name=DimensionType.PRICE,
            unit="$/unit",
            agent1_min=10.0,
            agent1_max=20.0,
            agent2_min=8.0,
            agent2_max=15.0
        ),
        NegotiationDimension(
            name=DimensionType.PAYMENT_TERMS,
            unit="days",
            agent1_min=30,
            agent1_max=90,
            agent2_min=15,
            agent2_max=60
        ),
        NegotiationDimension(
            name=DimensionType.CONTRACT_DURATION,
            unit="months",
            agent1_min=6,
            agent1_max=24,
            agent2_min=12,
            agent2_max=36
        )
    ]


@pytest.fixture
def sample_negotiation(sample_agent_1, sample_agent_2, sample_dimensions):
    """Create a sample negotiation state."""
    return NegotiationState(
        agent1_id=sample_agent_1.id,
        agent2_id=sample_agent_2.id,
        max_rounds=10,
        dimensions=sample_dimensions
    )


@pytest.fixture
def sample_offer_1(sample_agent_1):
    """Create a sample offer from agent 1."""
    return NegotiationOffer(
        agent_id=sample_agent_1.id,
        turn_number=1,
        volume=3000,
        price=15.0,
        payment_terms=60,
        contract_duration=12,
        message="I propose 3000 units at $15 per unit with 60-day payment terms for a 12-month contract.",
        confidence=0.8
    )


@pytest.fixture
def sample_offer_2(sample_agent_2):
    """Create a sample offer from agent 2."""
    return NegotiationOffer(
        agent_id=sample_agent_2.id,
        turn_number=2,
        volume=4000,
        price=12.0,
        payment_terms=45,
        contract_duration=18,
        message="I counter with 4000 units at $12 per unit with 45-day payment terms for an 18-month contract.",
        confidence=0.7
    )


@pytest.fixture
def sample_csv_tactics_content():
    """Sample CSV content for tactics import testing."""
    return """Aspect,Influencing Techniques,Negotiation Tactics
Focus,Persuading the person,Winning the negotiation
Approach,Psychological & relational,Strategic & positional
Timing,Often before/during negotiation,Mostly during negotiation
Tone,Often cooperative,Can be competitive or even aggressive
Risk,Lower (when sincere),Higher (may backfire if perceived as manipulative)"""


@pytest.fixture
def sample_csv_file(temp_dir, sample_csv_tactics_content):
    """Create a sample CSV file for testing."""
    csv_path = temp_dir / "test_tactics.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(sample_csv_tactics_content)
    return csv_path


# Mock data for testing edge cases
@pytest.fixture
def invalid_agent_config():
    """Create an invalid agent configuration for testing validation."""
    return {
        "name": "",  # Invalid: empty name
        "personality": {
            "openness": 1.5,  # Invalid: > 1.0
            "conscientiousness": -0.1,  # Invalid: < 0.0
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        },
        "power_level": {
            "level": 2.0,  # Invalid: > 1.0
            "description": "Invalid power level"
        },
        "zopa_boundaries": {
            "volume": {"min_acceptable": 5000, "max_desired": 1000}  # Invalid: min > max
        }
    }


@pytest.fixture
def overlapping_zopa_boundaries():
    """ZOPA boundaries with good overlap for testing."""
    return {
        "agent1": {
            "volume": {"min_acceptable": 1000, "max_desired": 5000},
            "price": {"min_acceptable": 10.0, "max_desired": 20.0}
        },
        "agent2": {
            "volume": {"min_acceptable": 2000, "max_desired": 4000},
            "price": {"min_acceptable": 12.0, "max_desired": 18.0}
        }
    }


@pytest.fixture
def non_overlapping_zopa_boundaries():
    """ZOPA boundaries with no overlap for testing."""
    return {
        "agent1": {
            "volume": {"min_acceptable": 1000, "max_desired": 2000},
            "price": {"min_acceptable": 20.0, "max_desired": 25.0}
        },
        "agent2": {
            "volume": {"min_acceptable": 3000, "max_desired": 5000},
            "price": {"min_acceptable": 10.0, "max_desired": 15.0}
        }
    }
