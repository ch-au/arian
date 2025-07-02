"""
Negotiation State and Flow Models

This module defines the data models for negotiation state management including:
- Negotiation dimensions and offers
- Turn-based flow tracking
- Negotiation results and analytics
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import uuid4
import datetime


class DimensionType(str, Enum):
    """Types of negotiation dimensions with their expected data types."""
    VOLUME = "volume"
    PRICE = "price"
    PAYMENT_TERMS = "payment_terms"
    CONTRACT_DURATION = "contract_duration"


class NegotiationDimension(BaseModel):
    """
    Represents a single dimension of negotiation (e.g., price, volume).
    
    Each dimension has a name, unit, and current state in the negotiation.
    """
    
    name: DimensionType = Field(..., description="The dimension being negotiated")
    unit: str = Field(..., description="Unit of measurement (e.g., 'units', '$/unit', 'days')")
    
    agent1_min: float = Field(..., description="Agent 1's minimum acceptable value")
    agent1_max: float = Field(..., description="Agent 1's maximum desired value")
    agent1_current: Optional[float] = Field(default=None, description="Agent 1's current offer")
    
    agent2_min: float = Field(..., description="Agent 2's minimum acceptable value")
    agent2_max: float = Field(..., description="Agent 2's maximum desired value")
    agent2_current: Optional[float] = Field(default=None, description="Agent 2's current offer")
    
    agreed_value: Optional[float] = Field(default=None, description="Final agreed value if reached")
    
    @validator('agent1_min', 'agent2_min')
    def validate_min_values(cls, v, values):
        """Ensure minimum values are reasonable."""
        if v < 0 and values.get('name') in [DimensionType.VOLUME, DimensionType.PRICE]:
            raise ValueError(f"Minimum value cannot be negative for {values.get('name')}")
        return v
    
    @validator('agent1_max', 'agent2_max')
    def validate_max_values(cls, v, values):
        """Ensure maximum values are greater than minimum values."""
        name = values.get('name')
        if name == DimensionType.VOLUME:
            agent1_min = values.get('agent1_min')
            agent2_min = values.get('agent2_min')
            if agent1_min is not None and v <= agent1_min:
                raise ValueError("Agent 1 max must be greater than min")
            if agent2_min is not None and v <= agent2_min:
                raise ValueError("Agent 2 max must be greater than min")
        return v
    
    def has_overlap(self) -> bool:
        """Check if there's any overlap between the two agents' ZOPA ranges."""
        return not (self.agent1_max < self.agent2_min or self.agent2_max < self.agent1_min)
    
    def get_overlap_range(self) -> Optional[tuple[float, float]]:
        """Get the overlapping range if it exists."""
        if not self.has_overlap():
            return None
        
        overlap_min = max(self.agent1_min, self.agent2_min)
        overlap_max = min(self.agent1_max, self.agent2_max)
        return (overlap_min, overlap_max)
    
    def is_value_acceptable_to_agent(self, value: float, agent_id: str) -> bool:
        """Check if a value is within an agent's acceptable range."""
        if agent_id == "agent1":
            return self.agent1_min <= value <= self.agent1_max
        elif agent_id == "agent2":
            return self.agent2_min <= value <= self.agent2_max
        else:
            raise ValueError(f"Invalid agent_id: {agent_id}")
    
    def get_concession_direction(self, agent_id: str) -> str:
        """Get the direction an agent needs to move to make concessions."""
        if agent_id == "agent1":
            if self.agent1_min < self.agent2_min:
                return "increase"  # Agent 1 needs to offer more
            else:
                return "decrease"  # Agent 1 needs to offer less
        elif agent_id == "agent2":
            if self.agent2_min < self.agent1_min:
                return "increase"  # Agent 2 needs to offer more
            else:
                return "decrease"  # Agent 2 needs to offer less
        else:
            raise ValueError(f"Invalid agent_id: {agent_id}")


class OfferStatus(str, Enum):
    """Status of a negotiation offer."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"


class NegotiationOffer(BaseModel):
    """
    Represents a complete offer made by an agent across all dimensions.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique offer identifier")
    agent_id: str = Field(..., description="ID of the agent making the offer")
    turn_number: int = Field(..., ge=1, description="Turn number when this offer was made")
    
    # Offer values for each dimension
    volume: int = Field(..., ge=0, description="Proposed volume in units")
    price: float = Field(..., ge=0, description="Proposed price per unit")
    payment_terms: int = Field(..., ge=0, le=365, description="Payment terms in days")
    contract_duration: int = Field(..., ge=1, le=120, description="Contract duration in months")
    
    # Metadata
    message: str = Field(..., description="Agent's message accompanying the offer")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Agent's confidence in this offer")
    reasoning: Optional[str] = Field(default=None, description="Agent's reasoning for this offer")
    
    status: OfferStatus = Field(default=OfferStatus.PENDING, description="Current status of the offer")
    response_message: Optional[str] = Field(default=None, description="Response message if rejected/countered")
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    def to_dict(self) -> Dict[str, Union[int, float, str]]:
        """Convert offer values to a dictionary for easy comparison."""
        return {
            "volume": self.volume,
            "price": self.price,
            "payment_terms": self.payment_terms,
            "contract_duration": self.contract_duration
        }
    
    def calculate_total_value(self) -> float:
        """Calculate the total monetary value of the offer."""
        return self.volume * self.price
    
    def is_within_zopa(self, dimensions: List[NegotiationDimension]) -> Dict[str, bool]:
        """Check if this offer is within ZOPA for each dimension."""
        results = {}
        offer_values = self.to_dict()
        
        for dimension in dimensions:
            value = offer_values.get(dimension.name.value)
            if value is not None:
                # Check if the offer is acceptable to the other agent
                other_agent = "agent2" if self.agent_id == "agent1" else "agent1"
                results[dimension.name.value] = dimension.is_value_acceptable_to_agent(value, other_agent)
            else:
                results[dimension.name.value] = False
        
        return results


class TurnType(str, Enum):
    """Type of turn in the negotiation."""
    OFFER = "offer"
    COUNTER_OFFER = "counter_offer"
    ACCEPTANCE = "acceptance"
    REJECTION = "rejection"
    WALK_AWAY = "walk_away"


class NegotiationTurn(BaseModel):
    """
    Represents a single turn in the negotiation process.
    """
    
    turn_number: int = Field(..., ge=1, description="Sequential turn number")
    agent_id: str = Field(..., description="ID of the agent taking this turn")
    turn_type: TurnType = Field(..., description="Type of action taken")
    
    offer: Optional[NegotiationOffer] = Field(default=None, description="Offer made (if applicable)")
    message: str = Field(..., description="Agent's communication for this turn")
    
    # Analysis data
    zopa_compliance: Optional[Dict[str, bool]] = Field(default=None, description="ZOPA compliance check")
    concession_analysis: Optional[Dict[str, float]] = Field(default=None, description="Concession amounts by dimension")
    
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    processing_time: Optional[float] = Field(default=None, description="Time taken to generate this turn (seconds)")


class NegotiationStatus(str, Enum):
    """Overall status of the negotiation."""
    SETUP = "setup"
    IN_PROGRESS = "in_progress"
    AGREEMENT_REACHED = "agreement_reached"
    FAILED_NO_AGREEMENT = "failed_no_agreement"
    FAILED_WALK_AWAY = "failed_walk_away"
    FAILED_MAX_ROUNDS = "failed_max_rounds"
    FAILED_ERROR = "failed_error"


class NegotiationResult(BaseModel):
    """
    Final result and analysis of a completed negotiation.
    """
    
    status: NegotiationStatus = Field(..., description="Final status of the negotiation")
    final_agreement: Optional[Dict[str, Union[int, float]]] = Field(default=None, description="Final agreed terms")
    
    total_turns: int = Field(..., ge=0, description="Total number of turns taken")
    duration_seconds: float = Field(..., ge=0, description="Total negotiation duration")
    
    # Success metrics
    agreement_reached: bool = Field(..., description="Whether an agreement was reached")
    mutual_satisfaction: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Estimated mutual satisfaction")
    
    # Agent performance
    agent1_concessions: Dict[str, float] = Field(default_factory=dict, description="Concessions made by agent 1")
    agent2_concessions: Dict[str, float] = Field(default_factory=dict, description="Concessions made by agent 2")
    
    # ZOPA analysis
    zopa_utilization: Dict[str, float] = Field(default_factory=dict, description="How much of ZOPA was utilized")
    dimensions_in_zopa: Dict[str, bool] = Field(default_factory=dict, description="Which dimensions ended in ZOPA")
    
    # Communication analysis
    total_messages: int = Field(default=0, description="Total messages exchanged")
    avg_message_length: float = Field(default=0.0, description="Average message length")
    
    failure_reason: Optional[str] = Field(default=None, description="Reason for failure if applicable")
    
    def get_success_score(self) -> float:
        """Calculate an overall success score (0-1)."""
        if not self.agreement_reached:
            return 0.0
        
        score = 0.5  # Base score for reaching agreement
        
        # Add points for ZOPA compliance
        if self.dimensions_in_zopa:
            zopa_compliance_rate = sum(self.dimensions_in_zopa.values()) / len(self.dimensions_in_zopa)
            score += 0.3 * zopa_compliance_rate
        
        # Add points for mutual satisfaction
        if self.mutual_satisfaction is not None:
            score += 0.2 * self.mutual_satisfaction
        
        return min(score, 1.0)


class NegotiationState(BaseModel):
    """
    Complete state of an ongoing or completed negotiation.
    
    This is the main model that tracks the entire negotiation process.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique negotiation identifier")
    
    # Participants
    agent1_id: str = Field(..., description="ID of the first agent")
    agent2_id: str = Field(..., description="ID of the second agent")
    
    # Configuration
    max_rounds: int = Field(default=20, ge=1, le=100, description="Maximum number of rounds")
    dimensions: List[NegotiationDimension] = Field(..., description="Negotiation dimensions")
    
    # State tracking
    status: NegotiationStatus = Field(default=NegotiationStatus.SETUP, description="Current negotiation status")
    current_round: int = Field(default=0, ge=0, description="Current round number")
    current_turn_agent: Optional[str] = Field(default=None, description="Agent whose turn it is")
    
    # History
    turns: List[NegotiationTurn] = Field(default_factory=list, description="Complete turn history")
    offers: List[NegotiationOffer] = Field(default_factory=list, description="All offers made")
    
    # Timestamps
    started_at: Optional[datetime.datetime] = Field(default=None, description="When negotiation started")
    ended_at: Optional[datetime.datetime] = Field(default=None, description="When negotiation ended")
    
    # Results
    result: Optional[NegotiationResult] = Field(default=None, description="Final result if completed")
    
    def start_negotiation(self) -> None:
        """Initialize the negotiation and set it to in-progress."""
        if self.status != NegotiationStatus.SETUP:
            raise ValueError("Negotiation can only be started from SETUP status")
        
        self.status = NegotiationStatus.IN_PROGRESS
        self.started_at = datetime.datetime.now()
        self.current_round = 1
        self.current_turn_agent = self.agent1_id  # Agent 1 goes first
    
    def add_turn(self, turn: NegotiationTurn) -> None:
        """Add a new turn to the negotiation."""
        if self.status != NegotiationStatus.IN_PROGRESS:
            raise ValueError("Cannot add turns to a negotiation that is not in progress")
        
        # Validate turn number
        expected_turn = len(self.turns) + 1
        if turn.turn_number != expected_turn:
            turn.turn_number = expected_turn
        
        self.turns.append(turn)
        
        # Add offer to offers list if present
        if turn.offer:
            self.offers.append(turn.offer)
        
        # Update current turn agent
        self.current_turn_agent = self.agent2_id if turn.agent_id == self.agent1_id else self.agent1_id
        
        # Check if we need to increment round (after both agents have taken a turn)
        if len(self.turns) % 2 == 0:
            self.current_round += 1
    
    def get_latest_offer_by_agent(self, agent_id: str) -> Optional[NegotiationOffer]:
        """Get the most recent offer made by a specific agent."""
        agent_offers = [offer for offer in self.offers if offer.agent_id == agent_id]
        return agent_offers[-1] if agent_offers else None
    
    def get_latest_offers(self) -> Dict[str, Optional[NegotiationOffer]]:
        """Get the latest offers from both agents."""
        return {
            self.agent1_id: self.get_latest_offer_by_agent(self.agent1_id),
            self.agent2_id: self.get_latest_offer_by_agent(self.agent2_id)
        }
    
    def check_agreement(self) -> bool:
        """Check if the latest offers from both agents constitute an agreement."""
        latest_offers = self.get_latest_offers()
        
        if not all(latest_offers.values()):
            return False  # Both agents must have made offers
        
        offer1 = latest_offers[self.agent1_id]
        offer2 = latest_offers[self.agent2_id]
        
        # Check if offers are identical across all dimensions
        return (
            offer1.volume == offer2.volume and
            offer1.price == offer2.price and
            offer1.payment_terms == offer2.payment_terms and
            offer1.contract_duration == offer2.contract_duration
        )
    
    def should_terminate(self) -> tuple[bool, str]:
        """
        Check if the negotiation should terminate and return the reason.
        
        Returns:
            (should_terminate, reason)
        """
        # Check for agreement
        if self.check_agreement():
            return True, "agreement_reached"
        
        # Check for max rounds
        if self.current_round > self.max_rounds:
            return True, "max_rounds_exceeded"
        
        # Check for walk-away in recent turns
        recent_turns = self.turns[-2:] if len(self.turns) >= 2 else self.turns
        for turn in recent_turns:
            if turn.turn_type == TurnType.WALK_AWAY:
                return True, "walk_away"
        
        return False, ""
    
    def finalize_negotiation(self, reason: str) -> NegotiationResult:
        """Finalize the negotiation and generate results."""
        self.ended_at = datetime.datetime.now()
        
        # Determine final status
        if reason == "agreement_reached":
            self.status = NegotiationStatus.AGREEMENT_REACHED
        elif reason == "max_rounds_exceeded":
            self.status = NegotiationStatus.FAILED_MAX_ROUNDS
        elif reason == "walk_away":
            self.status = NegotiationStatus.FAILED_WALK_AWAY
        else:
            self.status = NegotiationStatus.FAILED_NO_AGREEMENT
        
        # Calculate duration
        duration = (self.ended_at - self.started_at).total_seconds() if self.started_at else 0.0
        
        # Generate result
        self.result = NegotiationResult(
            status=self.status,
            total_turns=len(self.turns),
            duration_seconds=duration,
            agreement_reached=(reason == "agreement_reached"),
            failure_reason=reason if reason != "agreement_reached" else None
        )
        
        # Add final agreement if reached
        if reason == "agreement_reached":
            latest_offers = self.get_latest_offers()
            if all(latest_offers.values()):
                final_offer = list(latest_offers.values())[0]  # Both should be identical
                self.result.final_agreement = final_offer.to_dict()
        
        return self.result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current negotiation state."""
        return {
            "id": self.id,
            "status": self.status.value,
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "total_turns": len(self.turns),
            "total_offers": len(self.offers),
            "agents": [self.agent1_id, self.agent2_id],
            "dimensions": [dim.name.value for dim in self.dimensions],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }
