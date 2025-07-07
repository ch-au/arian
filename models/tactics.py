"""
Negotiation Tactics Models

This module defines the data models for negotiation tactics including:
- Individual tactic definitions
- Tactic library management
- CSV import/export functionality
"""

from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field, validator
from enum import Enum
import csv
import json
from pathlib import Path


class TacticAspect(str, Enum):
    """Categories of negotiation tactics based on their primary focus."""
    FOCUS = "Focus"
    APPROACH = "Approach"
    TIMING = "Timing"
    TONE = "Tone"
    RISK = "Risk"


class TacticType(str, Enum):
    """Types of negotiation techniques."""
    INFLUENCING = "Influencing Techniques"
    NEGOTIATION = "Negotiation Tactics"


class NegotiationTactic(BaseModel):
    """
    Represents a single negotiation tactic that can be used by agents.
    
    Based on the provided data format:
    Aspect | Influencing Techniques | Negotiation Tactics
    Focus  | Persuading the person  | Winning the negotiation
    """
    
    id: str = Field(..., description="Unique identifier for the tactic")
    name: str = Field(..., min_length=1, description="Human-readable name of the tactic")
    
    aspect: TacticAspect = Field(
        ...,
        description="The aspect this tactic addresses (Focus, Approach, Timing, Tone, Risk)"
    )
    
    tactic_type: TacticType = Field(
        ...,
        description="Whether this is an influencing technique or negotiation tactic"
    )
    
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed description of how to apply this tactic"
    )
    
    prompt_modifier: str = Field(
        ...,
        min_length=1,
        description="Text to add to agent prompts when this tactic is selected"
    )
    
    effectiveness_weight: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Multiplier for tactic effectiveness (0.1 = very weak, 2.0 = very strong)"
    )
    
    personality_affinity: Dict[str, float] = Field(
        default_factory=dict,
        description="How well this tactic works with different personality traits (0-1 scale)"
    )
    
    power_level_modifier: float = Field(
        default=0.0,
        ge=-0.5,
        le=0.5,
        description="How this tactic affects perceived power level (-0.5 to +0.5)"
    )
    
    risk_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Risk level of using this tactic (0 = safe, 1 = high risk)"
    )
    
    @validator('personality_affinity')
    def validate_personality_affinity(cls, v):
        """Validate personality affinity scores."""
        valid_traits = {'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'}
        
        for trait, score in v.items():
            if trait not in valid_traits:
                raise ValueError(f"Invalid personality trait: {trait}")
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Personality affinity score must be between 0.0 and 1.0, got {score}")
        
        return v
    
    def get_effectiveness_for_personality(self, personality_traits: Dict[str, float]) -> float:
        """
        Calculate how effective this tactic would be for a given personality.
        
        Args:
            personality_traits: Dict with Big 5 trait scores (0-1)
            
        Returns:
            Effectiveness score (0-2, where 1 is baseline)
        """
        if not self.personality_affinity:
            return self.effectiveness_weight
            
        affinity_score = 0.0
        trait_count = 0
        
        for trait, agent_score in personality_traits.items():
            if trait in self.personality_affinity:
                tactic_affinity = self.personality_affinity[trait]
                # Calculate how well the agent's trait level matches the tactic's preference
                affinity_score += 1.0 - abs(agent_score - tactic_affinity)
                trait_count += 1
        
        if trait_count == 0:
            return self.effectiveness_weight
            
        # Average affinity (0-1) multiplied by base effectiveness
        avg_affinity = affinity_score / trait_count
        return self.effectiveness_weight * avg_affinity
    
    def get_risk_description(self) -> str:
        """Get a human-readable description of the tactic's risk level."""
        if self.risk_level >= 0.8:
            return "High Risk - May backfire if perceived as manipulative"
        elif self.risk_level >= 0.6:
            return "Moderate Risk - Use with caution"
        elif self.risk_level >= 0.4:
            return "Low-Moderate Risk - Generally safe"
        elif self.risk_level >= 0.2:
            return "Low Risk - Safe to use"
        else:
            return "Very Low Risk - Minimal chance of negative consequences"
    
    def calculate_personality_compatibility(self, personality_profile) -> float:
        """
        Calculate compatibility score between this tactic and a personality profile.
        
        Args:
            personality_profile: PersonalityProfile object with Big 5 traits
            
        Returns:
            Compatibility score (0-1, where 1 is perfect match)
        """
        if not self.personality_affinity:
            return 0.5  # Neutral compatibility if no affinity defined
            
        compatibility_scores = []
        
        # Get personality traits as dict
        personality_traits = {
            'openness': personality_profile.openness,
            'conscientiousness': personality_profile.conscientiousness,
            'extraversion': personality_profile.extraversion,
            'agreeableness': personality_profile.agreeableness,
            'neuroticism': personality_profile.neuroticism
        }
        
        for trait, agent_score in personality_traits.items():
            if trait in self.personality_affinity:
                tactic_preference = self.personality_affinity[trait]
                # Calculate how well the agent's trait level matches the tactic's preference
                compatibility = 1.0 - abs(agent_score - tactic_preference)
                compatibility_scores.append(compatibility)
        
        if not compatibility_scores:
            return 0.5  # Neutral if no matching traits
            
        # Return average compatibility
        return sum(compatibility_scores) / len(compatibility_scores)


class TacticLibrary(BaseModel):
    """
    Collection of negotiation tactics with management functionality.
    
    Provides methods to load, save, filter, and manage tactics.
    """
    
    tactics: List[NegotiationTactic] = Field(
        default_factory=list,
        description="List of available tactics"
    )
    
    version: str = Field(
        default="1.0",
        description="Version of the tactic library"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Description of this tactic library"
    )
    
    def add_tactic(self, tactic: NegotiationTactic) -> None:
        """Add a new tactic to the library."""
        # Check for duplicate IDs
        if any(t.id == tactic.id for t in self.tactics):
            raise ValueError(f"Tactic with ID '{tactic.id}' already exists")
        
        self.tactics.append(tactic)
    
    def remove_tactic(self, tactic_id: str) -> bool:
        """Remove a tactic by ID. Returns True if removed, False if not found."""
        original_length = len(self.tactics)
        self.tactics = [t for t in self.tactics if t.id != tactic_id]
        return len(self.tactics) < original_length
    
    def get_tactic(self, tactic_id: str) -> Optional[NegotiationTactic]:
        """Get a tactic by ID."""
        for tactic in self.tactics:
            if tactic.id == tactic_id:
                return tactic
        return None
    
    def get_tactics_by_aspect(self, aspect: TacticAspect) -> List[NegotiationTactic]:
        """Get all tactics for a specific aspect."""
        return [t for t in self.tactics if t.aspect == aspect]
    
    def get_tactics_by_type(self, tactic_type: TacticType) -> List[NegotiationTactic]:
        """Get all tactics of a specific type."""
        return [t for t in self.tactics if t.tactic_type == tactic_type]
    
    def get_recommended_tactics(
        self,
        personality_traits: Dict[str, float],
        max_risk_level: float = 0.7,
        min_effectiveness: float = 0.5
    ) -> List[NegotiationTactic]:
        """
        Get tactics recommended for a specific personality profile.
        
        Args:
            personality_traits: Big 5 personality scores
            max_risk_level: Maximum acceptable risk level
            min_effectiveness: Minimum effectiveness threshold
            
        Returns:
            List of recommended tactics sorted by effectiveness
        """
        recommended = []
        
        for tactic in self.tactics:
            if tactic.risk_level > max_risk_level:
                continue
                
            effectiveness = tactic.get_effectiveness_for_personality(personality_traits)
            if effectiveness >= min_effectiveness:
                recommended.append((tactic, effectiveness))
        
        # Sort by effectiveness (descending)
        recommended.sort(key=lambda x: x[1], reverse=True)
        return [tactic for tactic, _ in recommended]
    
    def get_compatible_tactics(self, personality_profile, threshold: float = 0.5) -> List[NegotiationTactic]:
        """
        Get tactics that are compatible with a personality profile.
        
        Args:
            personality_profile: PersonalityProfile object with Big 5 traits
            threshold: Minimum compatibility threshold (0-1)
            
        Returns:
            List of compatible tactics sorted by compatibility score
        """
        compatible = []
        
        for tactic in self.tactics:
            compatibility = tactic.calculate_personality_compatibility(personality_profile)
            if compatibility > threshold:
                compatible.append((tactic, compatibility))
        
        # Sort by compatibility (descending)
        compatible.sort(key=lambda x: x[1], reverse=True)
        return [tactic for tactic, _ in compatible]
    
    def get_tactics_summary(self) -> Dict[str, Any]:
        """Get a summary of the tactic library."""
        aspect_counts = {}
        type_counts = {}
        risk_distribution = {"low": 0, "medium": 0, "high": 0}
        
        for tactic in self.tactics:
            # Count by aspect
            aspect_counts[tactic.aspect.value] = aspect_counts.get(tactic.aspect.value, 0) + 1
            
            # Count by type
            type_counts[tactic.tactic_type.value] = type_counts.get(tactic.tactic_type.value, 0) + 1
            
            # Risk distribution
            if tactic.risk_level < 0.4:
                risk_distribution["low"] += 1
            elif tactic.risk_level < 0.7:
                risk_distribution["medium"] += 1
            else:
                risk_distribution["high"] += 1
        
        return {
            "total_tactics": len(self.tactics),
            "by_aspect": aspect_counts,
            "by_type": type_counts,
            "risk_distribution": risk_distribution,
            "version": self.version
        }
    
    @classmethod
    def from_csv(cls, csv_path: Path) -> "TacticLibrary":
        """
        Load tactics from a CSV file.
        
        Expected CSV format:
        Aspect,Influencing Techniques,Negotiation Tactics
        Focus,Persuading the person,Winning the negotiation
        """
        library = cls()
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_idx, row in enumerate(reader):
                try:
                    # Extract aspect
                    aspect = row.get('Aspect', '').strip()
                    if not aspect:
                        continue
                    
                    # Create tactics for both influencing techniques and negotiation tactics
                    influencing = row.get('Influencing Techniques', '').strip()
                    negotiation = row.get('Negotiation Tactics', '').strip()
                    
                    if influencing:
                        tactic = NegotiationTactic(
                            id=f"inf_{aspect.lower()}_{row_idx}",
                            name=influencing,
                            aspect=TacticAspect(aspect),
                            tactic_type=TacticType.INFLUENCING,
                            description=f"Influencing technique focused on {aspect.lower()}: {influencing}",
                            prompt_modifier=f"Use {influencing.lower()} approach focusing on {aspect.lower()}."
                        )
                        library.add_tactic(tactic)
                    
                    if negotiation:
                        tactic = NegotiationTactic(
                            id=f"neg_{aspect.lower()}_{row_idx}",
                            name=negotiation,
                            aspect=TacticAspect(aspect),
                            tactic_type=TacticType.NEGOTIATION,
                            description=f"Negotiation tactic focused on {aspect.lower()}: {negotiation}",
                            prompt_modifier=f"Apply {negotiation.lower()} strategy with emphasis on {aspect.lower()}."
                        )
                        library.add_tactic(tactic)
                        
                except Exception as e:
                    print(f"Warning: Skipping row {row_idx} due to error: {e}")
                    continue
        
        return library
    
    def to_json(self, json_path: Path) -> None:
        """Save the tactic library to a JSON file."""
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(self.dict(), file, indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_path: Path) -> "TacticLibrary":
        """Load a tactic library from a JSON file."""
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return cls(**data)
