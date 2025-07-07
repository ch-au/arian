"""
Turn Manager

This module manages the turn-based flow of negotiations, ensuring proper sequencing
and validation of agent actions.
"""

from typing import Dict, List, Optional, Any
import logging
from enum import Enum

from models.negotiation import (
    NegotiationState,
    NegotiationTurn,
    NegotiationOffer,
    TurnType,
    NegotiationStatus
)
from models.agent import AgentConfig

logger = logging.getLogger(__name__)


class TurnValidationResult(Enum):
    """Results of turn validation."""
    VALID = "valid"
    INVALID_AGENT = "invalid_agent"
    INVALID_SEQUENCE = "invalid_sequence"
    INVALID_STATE = "invalid_state"
    INVALID_OFFER = "invalid_offer"


class TurnManager:
    """
    Manages the turn-based flow of negotiations.
    
    Ensures proper sequencing, validates turn actions, and maintains
    the integrity of the negotiation process.
    """
    
    def __init__(self):
        """Initialize the turn manager."""
        self.logger = logging.getLogger(__name__)
    
    def validate_turn(
        self,
        negotiation: NegotiationState,
        agent_id: str,
        turn_type: TurnType,
        offer: Optional[NegotiationOffer] = None
    ) -> TurnValidationResult:
        """
        Validate if a turn is allowed in the current negotiation state.
        
        Args:
            negotiation: Current negotiation state
            agent_id: ID of the agent attempting the turn
            turn_type: Type of turn being attempted
            offer: Offer being made (if applicable)
            
        Returns:
            Validation result
        """
        # Check if negotiation is in valid state for turns
        if negotiation.status != NegotiationStatus.IN_PROGRESS:
            self.logger.warning(f"Turn attempted on negotiation not in progress: {negotiation.status}")
            return TurnValidationResult.INVALID_STATE
        
        # Check if it's the correct agent's turn
        if negotiation.current_turn_agent != agent_id:
            self.logger.warning(f"Turn attempted by wrong agent: {agent_id}, expected: {negotiation.current_turn_agent}")
            return TurnValidationResult.INVALID_AGENT
        
        # Validate agent ID
        if agent_id not in [negotiation.agent1_id, negotiation.agent2_id]:
            self.logger.error(f"Invalid agent ID: {agent_id}")
            return TurnValidationResult.INVALID_AGENT
        
        # Validate turn sequence
        if not self._is_valid_turn_sequence(negotiation, turn_type):
            self.logger.warning(f"Invalid turn sequence: {turn_type}")
            return TurnValidationResult.INVALID_SEQUENCE
        
        # Validate offer if provided
        if turn_type in [TurnType.OFFER, TurnType.COUNTER_OFFER]:
            if not offer:
                self.logger.error(f"Offer required for turn type: {turn_type}")
                return TurnValidationResult.INVALID_OFFER
            
            if not self._validate_offer_structure(offer, negotiation):
                return TurnValidationResult.INVALID_OFFER
        
        return TurnValidationResult.VALID
    
    def _is_valid_turn_sequence(self, negotiation: NegotiationState, turn_type: TurnType) -> bool:
        """Check if the turn type is valid given the current negotiation history."""
        if not negotiation.turns:
            # First turn must be an offer
            return turn_type == TurnType.OFFER
        
        last_turn = negotiation.turns[-1]
        
        # Define valid turn transitions
        valid_transitions = {
            TurnType.OFFER: [TurnType.OFFER, TurnType.COUNTER_OFFER, TurnType.ACCEPTANCE, TurnType.REJECTION, TurnType.WALK_AWAY],
            TurnType.COUNTER_OFFER: [TurnType.COUNTER_OFFER, TurnType.ACCEPTANCE, TurnType.REJECTION, TurnType.WALK_AWAY],
            TurnType.ACCEPTANCE: [],  # Negotiation should end after acceptance
            TurnType.REJECTION: [TurnType.OFFER, TurnType.COUNTER_OFFER, TurnType.WALK_AWAY],
            TurnType.WALK_AWAY: []  # Negotiation should end after walk away
        }
        
        return turn_type in valid_transitions.get(last_turn.turn_type, [])
    
    def _validate_offer_structure(self, offer: NegotiationOffer, negotiation: NegotiationState) -> bool:
        """Validate the structure and content of an offer."""
        try:
            # Check required fields
            if not offer.message or len(offer.message.strip()) == 0:
                self.logger.error("Offer missing message")
                return False
            
            # Check dimension values are reasonable
            if offer.volume <= 0:
                self.logger.error(f"Invalid volume: {offer.volume}")
                return False
            
            if offer.price <= 0:
                self.logger.error(f"Invalid price: {offer.price}")
                return False
            
            if not 0 <= offer.payment_terms <= 365:
                self.logger.error(f"Invalid payment terms: {offer.payment_terms}")
                return False
            
            if not 1 <= offer.contract_duration <= 120:
                self.logger.error(f"Invalid contract duration: {offer.contract_duration}")
                return False
            
            # Check confidence is in valid range
            if not 0.0 <= offer.confidence <= 1.0:
                self.logger.error(f"Invalid confidence: {offer.confidence}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating offer structure: {e}")
            return False
    
    def get_next_agent(self, negotiation: NegotiationState) -> str:
        """
        Determine which agent should take the next turn.
        
        Args:
            negotiation: Current negotiation state
            
        Returns:
            ID of the agent who should take the next turn
        """
        if not negotiation.turns:
            # First turn goes to agent1
            return negotiation.agent1_id
        
        last_turn = negotiation.turns[-1]
        
        # Alternate between agents
        if last_turn.agent_id == negotiation.agent1_id:
            return negotiation.agent2_id
        else:
            return negotiation.agent1_id
    
    def get_turn_context(self, negotiation: NegotiationState, agent_id: str) -> Dict[str, Any]:
        """
        Get contextual information for an agent's turn.
        
        Args:
            negotiation: Current negotiation state
            agent_id: ID of the agent taking the turn
            
        Returns:
            Dictionary with turn context information
        """
        context = {
            'current_round': negotiation.current_round,
            'max_rounds': negotiation.max_rounds,
            'turn_number': len(negotiation.turns) + 1,
            'is_first_turn': len(negotiation.turns) == 0,
            'opponent_id': negotiation.agent2_id if agent_id == negotiation.agent1_id else negotiation.agent1_id,
            'negotiation_history': self._get_turn_history_summary(negotiation),
            'latest_offers': self._get_latest_offers(negotiation),
            'dimension_status': self._get_dimension_status(negotiation)
        }
        
        return context
    
    def _get_turn_history_summary(self, negotiation: NegotiationState) -> List[Dict[str, Any]]:
        """Get a summary of recent turns for context."""
        # Return last 5 turns for context
        recent_turns = negotiation.turns[-5:] if len(negotiation.turns) > 5 else negotiation.turns
        
        summary = []
        for turn in recent_turns:
            turn_summary = {
                'turn_number': turn.turn_number,
                'agent_id': turn.agent_id,
                'turn_type': turn.turn_type.value,
                'message': turn.message[:100] + "..." if len(turn.message) > 100 else turn.message,
                'has_offer': turn.offer is not None
            }
            
            if turn.offer:
                turn_summary['offer_summary'] = {
                    'volume': turn.offer.volume,
                    'price': turn.offer.price,
                    'payment_terms': turn.offer.payment_terms,
                    'contract_duration': turn.offer.contract_duration
                }
            
            summary.append(turn_summary)
        
        return summary
    
    def _get_latest_offers(self, negotiation: NegotiationState) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get the latest offers from both agents."""
        latest_offers = {
            negotiation.agent1_id: None,
            negotiation.agent2_id: None
        }
        
        # Find latest offer from each agent
        for offer in reversed(negotiation.offers):
            if latest_offers[offer.agent_id] is None:
                latest_offers[offer.agent_id] = {
                    'volume': offer.volume,
                    'price': offer.price,
                    'payment_terms': offer.payment_terms,
                    'contract_duration': offer.contract_duration,
                    'confidence': offer.confidence,
                    'turn_number': offer.turn_number
                }
        
        return latest_offers
    
    def _get_dimension_status(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """Get status of each negotiation dimension."""
        dimension_status = {}
        
        for dimension in negotiation.dimensions:
            status = {
                'name': dimension.name.value,
                'unit': dimension.unit,
                'has_overlap': dimension.has_overlap(),
                'agent1_range': {
                    'min': dimension.agent1_min,
                    'max': dimension.agent1_max,
                    'current': dimension.agent1_current
                },
                'agent2_range': {
                    'min': dimension.agent2_min,
                    'max': dimension.agent2_max,
                    'current': dimension.agent2_current
                }
            }
            
            if dimension.has_overlap():
                overlap_range = dimension.get_overlap_range()
                if overlap_range:
                    status['overlap_range'] = {
                        'min': overlap_range[0],
                        'max': overlap_range[1],
                        'size': overlap_range[1] - overlap_range[0]
                    }
            
            dimension_status[dimension.name.value] = status
        
        return dimension_status
    
    def calculate_turn_urgency(self, negotiation: NegotiationState) -> float:
        """
        Calculate urgency level for the current turn (0-1 scale).
        
        Higher urgency indicates approaching deadline or critical decision point.
        
        Args:
            negotiation: Current negotiation state
            
        Returns:
            Urgency score from 0.0 (low) to 1.0 (high)
        """
        urgency_factors = []
        
        # Round-based urgency
        round_progress = negotiation.current_round / negotiation.max_rounds
        urgency_factors.append(round_progress)
        
        # Turn-based urgency (within current round)
        turns_in_round = len(negotiation.turns) % 2
        if turns_in_round == 1:  # Second turn in round
            urgency_factors.append(0.6)
        else:  # First turn in round
            urgency_factors.append(0.3)
        
        # Convergence-based urgency
        if len(negotiation.offers) >= 4:  # Need at least 2 offers from each agent
            convergence_score = self._calculate_convergence_score(negotiation)
            # Low convergence = high urgency
            urgency_factors.append(1.0 - convergence_score)
        
        # ZOPA compliance urgency
        if negotiation.offers:
            latest_offer = negotiation.offers[-1]
            zopa_compliance = self._check_zopa_compliance_simple(latest_offer, negotiation)
            if not zopa_compliance:
                urgency_factors.append(0.8)  # High urgency if outside ZOPA
        
        return min(sum(urgency_factors) / len(urgency_factors), 1.0)
    
    def _calculate_convergence_score(self, negotiation: NegotiationState) -> float:
        """Calculate how much the offers are converging (0-1 scale)."""
        if len(negotiation.offers) < 4:
            return 0.0
        
        # Get offers from each agent
        agent1_offers = [offer for offer in negotiation.offers if offer.agent_id == negotiation.agent1_id]
        agent2_offers = [offer for offer in negotiation.offers if offer.agent_id == negotiation.agent2_id]
        
        if len(agent1_offers) < 2 or len(agent2_offers) < 2:
            return 0.0
        
        convergence_scores = []
        dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
        
        for dimension in dimensions:
            # Get latest values
            agent1_latest = getattr(agent1_offers[-1], dimension)
            agent2_latest = getattr(agent2_offers[-1], dimension)
            
            # Get initial values
            agent1_initial = getattr(agent1_offers[0], dimension)
            agent2_initial = getattr(agent2_offers[0], dimension)
            
            # Calculate convergence
            initial_distance = abs(agent1_initial - agent2_initial)
            current_distance = abs(agent1_latest - agent2_latest)
            
            if initial_distance > 0:
                convergence = (initial_distance - current_distance) / initial_distance
                convergence_scores.append(max(0.0, min(1.0, convergence)))
        
        return sum(convergence_scores) / len(convergence_scores) if convergence_scores else 0.0
    
    def _check_zopa_compliance_simple(self, offer: NegotiationOffer, negotiation: NegotiationState) -> bool:
        """Simple check if offer is within ZOPA boundaries."""
        offer_values = offer.to_dict()
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in offer_values:
                value = offer_values[dimension_name]
                
                # Check if value is acceptable to the other agent
                other_agent_id = negotiation.agent2_id if offer.agent_id == negotiation.agent1_id else negotiation.agent1_id
                
                if not dimension.is_value_acceptable_to_agent(value, other_agent_id):
                    return False
        
        return True
    
    def get_turn_recommendations(self, negotiation: NegotiationState, agent_id: str) -> Dict[str, Any]:
        """
        Get strategic recommendations for the current turn.
        
        Args:
            negotiation: Current negotiation state
            agent_id: ID of the agent taking the turn
            
        Returns:
            Dictionary with turn recommendations
        """
        recommendations = {
            'urgency_level': self.calculate_turn_urgency(negotiation),
            'suggested_actions': [],
            'concession_opportunities': [],
            'risk_factors': []
        }
        
        # Analyze current situation
        context = self.get_turn_context(negotiation, agent_id)
        
        # Generate action recommendations
        if context['is_first_turn']:
            recommendations['suggested_actions'].append("Make opening offer based on your preferred values")
        else:
            latest_offers = context['latest_offers']
            opponent_id = context['opponent_id']
            
            if opponent_id in latest_offers and latest_offers[opponent_id]:
                opponent_offer = latest_offers[opponent_id]
                recommendations['suggested_actions'].append("Analyze opponent's offer and prepare counter-offer")
                
                # Check for concession opportunities
                for dimension_name, status in context['dimension_status'].items():
                    if status['has_overlap']:
                        recommendations['concession_opportunities'].append(
                            f"Consider concessions on {dimension_name} within ZOPA range"
                        )
        
        # Add risk factors
        if recommendations['urgency_level'] > 0.7:
            recommendations['risk_factors'].append("High urgency - approaching deadline")
        
        if context['current_round'] > context['max_rounds'] * 0.8:
            recommendations['risk_factors'].append("Late in negotiation - consider final offers")
        
        return recommendations
