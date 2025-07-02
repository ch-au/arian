"""
Negotiation Context Models

This module defines data models for negotiation context including:
- Product/service information
- Negotiation history and background
- Market context and baseline values
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import uuid4
import datetime


class HistoryType(str, Enum):
    """Type of negotiation history between parties."""
    FIRST_CONTACT = "first_contact"
    RENEWAL = "renewal"
    RENEGOTIATION = "renegotiation"
    FOLLOW_UP = "follow_up"


class ProductCategory(str, Enum):
    """Product/service categories for context."""
    GOODS = "goods"
    SERVICES = "services"
    SOFTWARE = "software"
    CONSULTING = "consulting"
    MANUFACTURING = "manufacturing"
    RAW_MATERIALS = "raw_materials"
    OTHER = "other"


class MarketCondition(str, Enum):
    """Current market conditions affecting the negotiation."""
    BUYERS_MARKET = "buyers_market"
    SELLERS_MARKET = "sellers_market"
    BALANCED = "balanced"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class NegotiationContext(BaseModel):
    """
    Context information for a negotiation including product details,
    history, and market conditions.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique context identifier")
    
    # Product/Service Information
    product_name: str = Field(..., min_length=1, description="Name of the product or service")
    product_group: str = Field(..., min_length=1, description="Product group or category (e.g., 'Sweets', 'Electronics')")
    product_category: ProductCategory = Field(default=ProductCategory.GOODS, description="General product category")
    
    # Negotiation History
    history_type: HistoryType = Field(..., description="Type of negotiation history")
    previous_agreements: Optional[int] = Field(default=None, ge=0, description="Number of previous agreements")
    relationship_duration_months: Optional[int] = Field(default=None, ge=0, description="Length of business relationship in months")
    
    # Baseline Values
    baseline_volume: int = Field(..., ge=1, description="Current/baseline volume")
    baseline_price: float = Field(..., gt=0, description="Current/baseline price per unit")
    baseline_payment_terms: int = Field(default=30, ge=0, le=365, description="Current payment terms in days")
    baseline_contract_duration: int = Field(default=12, ge=1, le=120, description="Current contract duration in months")
    
    # Market Context
    market_condition: MarketCondition = Field(default=MarketCondition.BALANCED, description="Current market conditions")
    market_notes: Optional[str] = Field(default=None, description="Additional market context notes")
    
    # Urgency and Constraints
    urgency_level: float = Field(default=0.5, ge=0.0, le=1.0, description="Urgency level (0=no rush, 1=very urgent)")
    budget_constraints: Optional[str] = Field(default=None, description="Budget or financial constraints")
    timeline_constraints: Optional[str] = Field(default=None, description="Timeline or delivery constraints")
    
    # Additional Context
    special_requirements: Optional[str] = Field(default=None, description="Special requirements or considerations")
    competitive_situation: Optional[str] = Field(default=None, description="Competitive landscape information")
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    @validator('baseline_price')
    def validate_baseline_price(cls, v):
        """Ensure baseline price is reasonable."""
        if v <= 0:
            raise ValueError("Baseline price must be positive")
        if v > 1000000:  # Arbitrary large number check
            raise ValueError("Baseline price seems unreasonably high")
        return v
    
    @validator('baseline_volume')
    def validate_baseline_volume(cls, v):
        """Ensure baseline volume is reasonable."""
        if v <= 0:
            raise ValueError("Baseline volume must be positive")
        if v > 10000000:  # Arbitrary large number check
            raise ValueError("Baseline volume seems unreasonably high")
        return v
    
    def get_total_baseline_value(self) -> float:
        """Calculate total baseline contract value."""
        return self.baseline_volume * self.baseline_price
    
    def get_context_summary(self) -> str:
        """Generate a human-readable context summary."""
        summary_parts = [
            f"Product: {self.product_name} ({self.product_group})",
            f"History: {self.history_type.value.replace('_', ' ').title()}",
            f"Baseline: {self.baseline_volume:,} units @ ${self.baseline_price:.2f}/unit",
            f"Total Value: ${self.get_total_baseline_value():,.2f}"
        ]
        
        if self.relationship_duration_months:
            summary_parts.append(f"Relationship: {self.relationship_duration_months} months")
        
        if self.market_condition != MarketCondition.BALANCED:
            summary_parts.append(f"Market: {self.market_condition.value.replace('_', ' ').title()}")
        
        if self.urgency_level > 0.7:
            summary_parts.append("High Urgency")
        elif self.urgency_level < 0.3:
            summary_parts.append("Low Urgency")
        
        return " | ".join(summary_parts)
    
    def get_history_description(self) -> str:
        """Get a detailed description of the negotiation history."""
        if self.history_type == HistoryType.FIRST_CONTACT:
            return "This is the first negotiation between these parties."
        elif self.history_type == HistoryType.RENEWAL:
            duration_text = f" after {self.relationship_duration_months} months" if self.relationship_duration_months else ""
            agreements_text = f" ({self.previous_agreements} previous agreements)" if self.previous_agreements else ""
            return f"Contract renewal negotiation{duration_text}{agreements_text}."
        elif self.history_type == HistoryType.RENEGOTIATION:
            return "Renegotiation of existing contract terms."
        elif self.history_type == HistoryType.FOLLOW_UP:
            return "Follow-up negotiation to previous discussions."
        else:
            return "Negotiation with established relationship."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            "id": self.id,
            "product_name": self.product_name,
            "product_group": self.product_group,
            "product_category": self.product_category.value,
            "history_type": self.history_type.value,
            "baseline_volume": self.baseline_volume,
            "baseline_price": self.baseline_price,
            "baseline_payment_terms": self.baseline_payment_terms,
            "baseline_contract_duration": self.baseline_contract_duration,
            "market_condition": self.market_condition.value,
            "urgency_level": self.urgency_level,
            "total_baseline_value": self.get_total_baseline_value(),
            "context_summary": self.get_context_summary(),
            "history_description": self.get_history_description(),
            "created_at": self.created_at.isoformat()
        }


class KeyMomentType(str, Enum):
    """Types of key moments that can occur during negotiation."""
    OPENING_OFFER = "opening_offer"
    FIRST_CONCESSION = "first_concession"
    MAJOR_CONCESSION = "major_concession"
    DEADLOCK = "deadlock"
    BREAKTHROUGH = "breakthrough"
    ZOPA_VIOLATION = "zopa_violation"
    ZOPA_ENTRY = "zopa_entry"
    FINAL_OFFER = "final_offer"
    WALK_AWAY_THREAT = "walk_away_threat"
    AGREEMENT_REACHED = "agreement_reached"


class KeyMoment(BaseModel):
    """
    Represents a significant moment during the negotiation process.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique moment identifier")
    turn_number: int = Field(..., ge=1, description="Turn number when this moment occurred")
    moment_type: KeyMomentType = Field(..., description="Type of key moment")
    
    agent_id: str = Field(..., description="Agent who triggered this moment")
    description: str = Field(..., description="Human-readable description of the moment")
    
    # Impact Analysis
    impact_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Impact score (0=low, 1=high)")
    dimensions_affected: list[str] = Field(default_factory=list, description="Negotiation dimensions affected")
    
    # Context
    offer_values: Optional[Dict[str, float]] = Field(default=None, description="Offer values at this moment")
    concession_amounts: Optional[Dict[str, float]] = Field(default=None, description="Concession amounts if applicable")
    
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    def get_moment_summary(self) -> str:
        """Get a summary of this key moment."""
        moment_descriptions = {
            KeyMomentType.OPENING_OFFER: "Opening offer made",
            KeyMomentType.FIRST_CONCESSION: "First concession offered",
            KeyMomentType.MAJOR_CONCESSION: "Significant concession made",
            KeyMomentType.DEADLOCK: "Negotiation reached deadlock",
            KeyMomentType.BREAKTHROUGH: "Breakthrough achieved",
            KeyMomentType.ZOPA_VIOLATION: "Offer outside ZOPA boundaries",
            KeyMomentType.ZOPA_ENTRY: "Offer entered ZOPA zone",
            KeyMomentType.FINAL_OFFER: "Final offer presented",
            KeyMomentType.WALK_AWAY_THREAT: "Walk-away threat made",
            KeyMomentType.AGREEMENT_REACHED: "Agreement successfully reached"
        }
        
        base_description = moment_descriptions.get(self.moment_type, "Key moment occurred")
        return f"Turn {self.turn_number}: {base_description} - {self.description}"
    
    def is_positive_moment(self) -> bool:
        """Check if this is generally a positive moment for negotiation progress."""
        positive_moments = {
            KeyMomentType.BREAKTHROUGH,
            KeyMomentType.ZOPA_ENTRY,
            KeyMomentType.AGREEMENT_REACHED,
            KeyMomentType.FIRST_CONCESSION
        }
        return self.moment_type in positive_moments
    
    def is_critical_moment(self) -> bool:
        """Check if this is a critical moment requiring attention."""
        critical_moments = {
            KeyMomentType.DEADLOCK,
            KeyMomentType.WALK_AWAY_THREAT,
            KeyMomentType.ZOPA_VIOLATION,
            KeyMomentType.FINAL_OFFER
        }
        return self.moment_type in critical_moments or self.impact_score > 0.8
