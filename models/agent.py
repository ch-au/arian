"""
Agent Configuration Models

This module defines the data models for agent configuration including:
- Big 5 personality traits
- Power level in negotiations
- Agent configuration combining personality, tactics, and ZOPA
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import uuid4
import datetime


class PersonalityProfile(BaseModel):
    """
    Big 5 personality model for negotiation agents.
    
    Each trait is scored from 0.0 to 1.0:
    - 0.0 = Very low on this trait
    - 1.0 = Very high on this trait
    """
    
    openness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Openness to experience - creativity, curiosity, willingness to try new approaches"
    )
    
    conscientiousness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Conscientiousness - organization, attention to detail, systematic approach"
    )
    
    extraversion: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Extraversion - assertiveness, social confidence, communication style"
    )
    
    agreeableness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Agreeableness - cooperation, trust, willingness to compromise"
    )
    
    neuroticism: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Neuroticism - emotional stability, stress response, risk tolerance"
    )
    
    def get_negotiation_style_description(self) -> str:
        """Generate a human-readable description of the negotiation style based on personality."""
        style_elements = []
        
        if self.agreeableness > 0.7:
            style_elements.append("collaborative and cooperative")
        elif self.agreeableness < 0.3:
            style_elements.append("competitive and assertive")
        else:
            style_elements.append("balanced in cooperation")
            
        if self.conscientiousness > 0.7:
            style_elements.append("detail-oriented and systematic")
        elif self.conscientiousness < 0.3:
            style_elements.append("flexible and adaptable")
            
        if self.extraversion > 0.7:
            style_elements.append("confident and direct in communication")
        elif self.extraversion < 0.3:
            style_elements.append("thoughtful and reserved")
            
        if self.neuroticism > 0.7:
            style_elements.append("cautious and risk-averse")
        elif self.neuroticism < 0.3:
            style_elements.append("calm under pressure")
            
        if self.openness > 0.7:
            style_elements.append("creative in finding solutions")
        elif self.openness < 0.3:
            style_elements.append("prefers traditional approaches")
            
        return ", ".join(style_elements)
    
    def get_summary(self) -> str:
        """Get a summary of personality traits for display."""
        traits = []
        
        # Categorize each trait
        if self.openness >= 0.7:
            traits.append("High openness")
        elif self.openness <= 0.3:
            traits.append("Low openness")
        
        if self.conscientiousness >= 0.7:
            traits.append("High conscientiousness")
        elif self.conscientiousness <= 0.3:
            traits.append("Low conscientiousness")
        
        if self.extraversion >= 0.7:
            traits.append("High extraversion")
        elif self.extraversion <= 0.3:
            traits.append("Low extraversion")
        
        if self.agreeableness >= 0.7:
            traits.append("High agreeableness")
        elif self.agreeableness <= 0.3:
            traits.append("Low agreeableness")
        
        if self.neuroticism >= 0.7:
            traits.append("High neuroticism")
        elif self.neuroticism <= 0.3:
            traits.append("Low neuroticism")
        
        return ", ".join(traits) if traits else "Moderate personality traits"


class PowerLevel(BaseModel):
    """
    Represents the relative power level of an agent in the negotiation.
    
    Power affects:
    - Willingness to make concessions
    - Assertiveness in communication
    - Walk-away threshold
    """
    
    level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Power level from 0.0 (low power) to 1.0 (high power)"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the power source (e.g., 'market leader', 'urgent need')"
    )
    
    sources: List[str] = Field(
        default_factory=list,
        description="Sources of power (e.g., 'Position', 'Expertise', 'Network')"
    )
    
    def get_power_description(self) -> str:
        """Get a human-readable description of the power level."""
        if self.level >= 0.8:
            return "Very High Power - Strong negotiating position"
        elif self.level >= 0.6:
            return "High Power - Good alternatives available"
        elif self.level >= 0.4:
            return "Moderate Power - Balanced position"
        elif self.level >= 0.2:
            return "Low Power - Limited alternatives"
        else:
            return "Very Low Power - Weak negotiating position"
    
    def get_category(self) -> str:
        """Get a simple category for the power level."""
        if self.level >= 0.7:
            return "High"
        elif self.level >= 0.4:
            return "Medium"
        else:
            return "Low"


class AgentConfig(BaseModel):
    """
    Complete configuration for a negotiation agent.
    
    Combines personality, power level, tactics, and ZOPA boundaries
    to define how an agent will behave in negotiations.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique agent identifier")
    name: str = Field(..., min_length=1, description="Human-readable agent name")
    
    personality: PersonalityProfile = Field(
        default_factory=PersonalityProfile,
        description="Big 5 personality traits"
    )
    
    power_level: PowerLevel = Field(
        default_factory=PowerLevel,
        description="Relative power in the negotiation"
    )
    
    selected_tactics: List[str] = Field(
        default_factory=list,
        description="List of tactic IDs this agent will use"
    )
    
    zopa_boundaries: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="ZOPA boundaries for each negotiation dimension"
    )
    
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="When this configuration was created"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the agent's role or background"
    )
    
    @validator('selected_tactics')
    def validate_tactics(cls, v):
        """Ensure tactics list contains unique values."""
        if len(v) != len(set(v)):
            raise ValueError("Tactics list must contain unique values")
        return v
    
    @validator('zopa_boundaries')
    def validate_zopa_boundaries(cls, v):
        """Validate ZOPA boundary structure."""
        required_dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
        
        for dimension in required_dimensions:
            if dimension not in v:
                continue  # Allow partial configuration during setup
                
            boundary = v[dimension]
            if not isinstance(boundary, dict):
                raise ValueError(f"ZOPA boundary for {dimension} must be a dictionary")
                
            required_keys = ['min_acceptable', 'max_desired']
            for key in required_keys:
                if key not in boundary:
                    raise ValueError(f"ZOPA boundary for {dimension} missing {key}")
                    
                if not isinstance(boundary[key], (int, float)):
                    raise ValueError(f"ZOPA boundary {key} for {dimension} must be numeric")
                    
            if boundary['min_acceptable'] > boundary['max_desired']:
                raise ValueError(f"ZOPA boundary for {dimension}: min_acceptable cannot be greater than max_desired")
        
        return v
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent configuration for display."""
        return {
            "id": self.id,
            "name": self.name,
            "personality_style": self.personality.get_negotiation_style_description(),
            "power_level": self.power_level.get_power_description(),
            "tactics_count": len(self.selected_tactics),
            "configured_dimensions": list(self.zopa_boundaries.keys()),
            "created_at": self.created_at.isoformat()
        }
    
    def is_fully_configured(self) -> bool:
        """Check if the agent is fully configured for negotiation."""
        required_dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
        
        # Check if all dimensions have ZOPA boundaries
        for dimension in required_dimensions:
            if dimension not in self.zopa_boundaries:
                return False
                
        # Check if at least one tactic is selected
        if not self.selected_tactics:
            return False
            
        return True
    
    def get_zopa_for_dimension(self, dimension: str) -> Optional[Dict[str, float]]:
        """Get ZOPA boundaries for a specific dimension."""
        return self.zopa_boundaries.get(dimension)
    
    def set_zopa_for_dimension(self, dimension: str, min_acceptable: float, max_desired: float) -> None:
        """Set ZOPA boundaries for a specific dimension."""
        if min_acceptable > max_desired:
            raise ValueError(f"min_acceptable ({min_acceptable}) cannot be greater than max_desired ({max_desired})")
            
        self.zopa_boundaries[dimension] = {
            'min_acceptable': min_acceptable,
            'max_desired': max_desired
        }
