"""
Data Collector

Collects and processes negotiation data for analytics, including real-time
event tracking and performance data aggregation.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..storage.analytics_db import AnalyticsDatabase
from ..storage.data_models import (
    NegotiationAnalytics,
    AnalyticsEvent,
    AnalyticsEventType
)
from ..models.negotiation import NegotiationState, NegotiationOffer
from ..models.agent import AgentConfig


class DataCollector:
    """
    Collects and processes negotiation data for analytics.
    """
    
    def __init__(self, analytics_db: AnalyticsDatabase):
        """
        Initialize data collector.
        
        Args:
            analytics_db: Analytics database instance
        """
        self.db = analytics_db
        self._active_negotiations: Dict[str, Dict[str, Any]] = {}
    
    def start_negotiation_tracking(self, negotiation: NegotiationState, agent1: AgentConfig, agent2: AgentConfig) -> bool:
        """
        Start tracking a negotiation for analytics.
        
        Args:
            negotiation: Negotiation state
            agent1: First agent configuration
            agent2: Second agent configuration
            
        Returns:
            True if tracking started successfully
        """
        try:
            # Store negotiation context for analytics
            self._active_negotiations[negotiation.id] = {
                'negotiation': negotiation,
                'agent1': agent1,
                'agent2': agent2,
                'start_time': datetime.utcnow(),
                'events': []
            }
            
            # Record start event
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation.id,
                event_type=AnalyticsEventType.NEGOTIATION_START,
                event_data={
                    'agent1_id': agent1.id,
                    'agent2_id': agent2.id,
                    'max_rounds': negotiation.max_rounds,
                    'dimensions': len(negotiation.dimensions)
                }
            )
            
            self.db.save_analytics_event(event)
            self._active_negotiations[negotiation.id]['events'].append(event)
            
            return True
            
        except Exception as e:
            print(f"Error starting negotiation tracking: {e}")
            return False
    
    def record_turn_completed(self, negotiation_id: str, turn_number: int, agent_id: str, offer: Optional[NegotiationOffer] = None) -> bool:
        """
        Record a completed negotiation turn.
        
        Args:
            negotiation_id: Negotiation identifier
            turn_number: Turn number
            agent_id: Agent who completed the turn
            offer: Offer made (if any)
            
        Returns:
            True if recorded successfully
        """
        try:
            if negotiation_id not in self._active_negotiations:
                return False
            
            event_data = {
                'agent_id': agent_id,
                'turn_number': turn_number
            }
            
            if offer:
                event_data.update({
                    'offer': {
                        'volume': offer.volume,
                        'price': offer.price,
                        'payment_terms': offer.payment_terms,
                        'contract_duration': offer.contract_duration,
                        'confidence': offer.confidence
                    }
                })
            
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                event_type=AnalyticsEventType.TURN_COMPLETED,
                turn_number=turn_number,
                agent_id=agent_id,
                event_data=event_data
            )
            
            self.db.save_analytics_event(event)
            self._active_negotiations[negotiation_id]['events'].append(event)
            
            return True
            
        except Exception as e:
            print(f"Error recording turn: {e}")
            return False
    
    def record_agreement_reached(self, negotiation_id: str, final_agreement: Dict[str, Any]) -> bool:
        """
        Record that an agreement was reached.
        
        Args:
            negotiation_id: Negotiation identifier
            final_agreement: Final agreement terms
            
        Returns:
            True if recorded successfully
        """
        try:
            if negotiation_id not in self._active_negotiations:
                return False
            
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                event_type=AnalyticsEventType.AGREEMENT_REACHED,
                event_data={
                    'agreement': final_agreement,
                    'success': True
                },
                performance_impact=1.0  # Positive impact
            )
            
            self.db.save_analytics_event(event)
            self._active_negotiations[negotiation_id]['events'].append(event)
            
            return True
            
        except Exception as e:
            print(f"Error recording agreement: {e}")
            return False
    
    def record_negotiation_failed(self, negotiation_id: str, reason: str) -> bool:
        """
        Record that a negotiation failed.
        
        Args:
            negotiation_id: Negotiation identifier
            reason: Reason for failure
            
        Returns:
            True if recorded successfully
        """
        try:
            if negotiation_id not in self._active_negotiations:
                return False
            
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                event_type=AnalyticsEventType.NEGOTIATION_FAILED,
                event_data={
                    'reason': reason,
                    'success': False
                },
                performance_impact=-0.5  # Negative impact
            )
            
            self.db.save_analytics_event(event)
            self._active_negotiations[negotiation_id]['events'].append(event)
            
            return True
            
        except Exception as e:
            print(f"Error recording failure: {e}")
            return False
    
    def record_zopa_violation(self, negotiation_id: str, agent_id: str, dimension: str, violation_details: Dict[str, Any]) -> bool:
        """
        Record a ZOPA violation.
        
        Args:
            negotiation_id: Negotiation identifier
            agent_id: Agent who violated ZOPA
            dimension: Dimension where violation occurred
            violation_details: Details of the violation
            
        Returns:
            True if recorded successfully
        """
        try:
            if negotiation_id not in self._active_negotiations:
                return False
            
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                event_type=AnalyticsEventType.ZOPA_VIOLATION,
                agent_id=agent_id,
                event_data={
                    'dimension': dimension,
                    'violation_details': violation_details
                },
                performance_impact=-0.3  # Negative impact
            )
            
            self.db.save_analytics_event(event)
            self._active_negotiations[negotiation_id]['events'].append(event)
            
            return True
            
        except Exception as e:
            print(f"Error recording ZOPA violation: {e}")
            return False
    
    def record_tactic_applied(self, negotiation_id: str, agent_id: str, tactic_id: str, effectiveness: float) -> bool:
        """
        Record that a tactic was applied.
        
        Args:
            negotiation_id: Negotiation identifier
            agent_id: Agent who applied the tactic
            tactic_id: Tactic identifier
            effectiveness: Estimated effectiveness (0.0 to 1.0)
            
        Returns:
            True if recorded successfully
        """
        try:
            if negotiation_id not in self._active_negotiations:
                return False
            
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                event_type=AnalyticsEventType.TACTIC_APPLIED,
                agent_id=agent_id,
                event_data={
                    'tactic_id': tactic_id,
                    'effectiveness': effectiveness
                },
                performance_impact=effectiveness - 0.5  # Convert to -0.5 to +0.5 range
            )
            
            self.db.save_analytics_event(event)
            self._active_negotiations[negotiation_id]['events'].append(event)
            
            return True
            
        except Exception as e:
            print(f"Error recording tactic application: {e}")
            return False
    
    def finalize_negotiation_analytics(self, negotiation_id: str, final_state: NegotiationState) -> Optional[NegotiationAnalytics]:
        """
        Finalize analytics for a completed negotiation.
        
        Args:
            negotiation_id: Negotiation identifier
            final_state: Final negotiation state
            
        Returns:
            NegotiationAnalytics object if successful, None otherwise
        """
        try:
            if negotiation_id not in self._active_negotiations:
                return None
            
            tracking_data = self._active_negotiations[negotiation_id]
            negotiation = tracking_data['negotiation']
            agent1 = tracking_data['agent1']
            agent2 = tracking_data['agent2']
            start_time = tracking_data['start_time']
            end_time = datetime.utcnow()
            
            # Calculate metrics
            duration_seconds = (end_time - start_time).total_seconds()
            agreement_reached = final_state.status.value == 'agreement_reached'
            
            # Calculate success score
            success_score = self._calculate_success_score(final_state, tracking_data['events'])
            
            # Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score(final_state, duration_seconds)
            
            # Calculate agreement quality (if agreement reached)
            agreement_quality = None
            mutual_satisfaction = None
            final_agreement = None
            
            if agreement_reached and final_state.offers:
                final_offer = final_state.offers[-1]
                agreement_quality = self._calculate_agreement_quality(final_offer, negotiation.dimensions)
                mutual_satisfaction = self._calculate_mutual_satisfaction(final_offer, agent1, agent2)
                final_agreement = final_offer.to_dict()
            
            # Calculate ZOPA utilization
            zopa_utilization = self._calculate_zopa_utilization(final_state, negotiation.dimensions)
            
            # Count ZOPA violations
            zopa_violations = len([e for e in tracking_data['events'] if e.event_type == AnalyticsEventType.ZOPA_VIOLATION])
            
            # Get context information (simplified)
            product_category = "Premium Chocolate"  # Default - would be extracted from context
            market_condition = "Stable"  # Default - would be extracted from context
            baseline_values = {
                'volume': 3000,
                'price': 12.5,
                'payment_terms': 45,
                'contract_duration': 12
            }
            
            # Create analytics record
            analytics = NegotiationAnalytics(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                started_at=start_time,
                ended_at=end_time,
                duration_seconds=duration_seconds,
                agent1_id=agent1.id,
                agent2_id=agent2.id,
                agent1_personality=agent1.personality.dict(),
                agent2_personality=agent2.personality.dict(),
                agent1_tactics=agent1.selected_tactics,
                agent2_tactics=agent2.selected_tactics,
                agreement_reached=agreement_reached,
                total_turns=len(final_state.turns),
                total_rounds=final_state.current_round,
                success_score=success_score,
                efficiency_score=efficiency_score,
                agreement_quality=agreement_quality,
                mutual_satisfaction=mutual_satisfaction,
                zopa_utilization=zopa_utilization,
                zopa_violations=zopa_violations,
                final_agreement=final_agreement,
                product_category=product_category,
                market_condition=market_condition,
                baseline_values=baseline_values
            )
            
            # Save to database
            if self.db.save_negotiation_analytics(analytics):
                # Record end event
                end_event = AnalyticsEvent(
                    id=str(uuid.uuid4()),
                    negotiation_id=negotiation_id,
                    event_type=AnalyticsEventType.NEGOTIATION_END,
                    event_data={
                        'success': agreement_reached,
                        'duration_seconds': duration_seconds,
                        'total_turns': len(final_state.turns)
                    }
                )
                self.db.save_analytics_event(end_event)
                
                # Clean up tracking data
                del self._active_negotiations[negotiation_id]
                
                return analytics
            
            return None
            
        except Exception as e:
            print(f"Error finalizing negotiation analytics: {e}")
            return None
    
    def get_active_negotiations(self) -> List[str]:
        """Get list of currently tracked negotiations."""
        return list(self._active_negotiations.keys())
    
    def get_negotiation_events(self, negotiation_id: str) -> List[AnalyticsEvent]:
        """Get events for a specific negotiation."""
        if negotiation_id in self._active_negotiations:
            return self._active_negotiations[negotiation_id]['events']
        return self.db.get_negotiation_events(negotiation_id)
    
    def cleanup_stale_negotiations(self, max_age_hours: int = 24) -> int:
        """
        Clean up stale negotiation tracking data.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of negotiations cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale_negotiations = []
        
        for negotiation_id, data in self._active_negotiations.items():
            if data['start_time'] < cutoff_time:
                stale_negotiations.append(negotiation_id)
        
        for negotiation_id in stale_negotiations:
            del self._active_negotiations[negotiation_id]
        
        return len(stale_negotiations)
    
    # Helper methods for calculations
    
    def _calculate_success_score(self, final_state: NegotiationState, events: List[AnalyticsEvent]) -> float:
        """Calculate overall success score for the negotiation."""
        base_score = 1.0 if final_state.status.value == 'agreement_reached' else 0.0
        
        # Adjust based on efficiency
        if final_state.current_round <= final_state.max_rounds // 2:
            base_score += 0.2  # Bonus for efficiency
        
        # Adjust based on events
        for event in events:
            if event.performance_impact:
                base_score += event.performance_impact * 0.1  # Small adjustments
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_efficiency_score(self, final_state: NegotiationState, duration_seconds: float) -> float:
        """Calculate efficiency score based on time and turns."""
        # Base efficiency on rounds used vs max rounds
        round_efficiency = 1.0 - (final_state.current_round / final_state.max_rounds)
        
        # Base efficiency on time (assuming 30 seconds per turn is optimal)
        optimal_duration = len(final_state.turns) * 30
        time_efficiency = min(1.0, optimal_duration / duration_seconds) if duration_seconds > 0 else 1.0
        
        return (round_efficiency + time_efficiency) / 2
    
    def _calculate_agreement_quality(self, final_offer: NegotiationOffer, dimensions: List) -> float:
        """Calculate quality of the final agreement."""
        # Simplified quality calculation based on offer confidence and ZOPA utilization
        base_quality = final_offer.confidence or 0.7
        
        # Would include more sophisticated quality metrics in practice
        return min(1.0, base_quality)
    
    def _calculate_mutual_satisfaction(self, final_offer: NegotiationOffer, agent1: AgentConfig, agent2: AgentConfig) -> float:
        """Calculate mutual satisfaction with the agreement."""
        # Simplified calculation - would use actual ZOPA analysis in practice
        return 0.75  # Default satisfaction score
    
    def _calculate_zopa_utilization(self, final_state: NegotiationState, dimensions: List) -> Dict[str, float]:
        """Calculate ZOPA utilization by dimension."""
        utilization = {}
        
        if final_state.offers:
            final_offer = final_state.offers[-1]
            
            # Simplified utilization calculation
            utilization = {
                'volume': 0.7,
                'price': 0.8,
                'payment_terms': 0.6,
                'contract_duration': 0.75
            }
        
        return utilization
    
    def export_negotiation_data(self, negotiation_id: str, export_path: Path) -> bool:
        """
        Export all data for a specific negotiation.
        
        Args:
            negotiation_id: Negotiation identifier
            export_path: Path to export file
            
        Returns:
            True if export successful
        """
        try:
            # Get analytics data
            analytics = self.db.get_negotiation_analytics(negotiation_id)
            events = self.db.get_negotiation_events(negotiation_id)
            
            if not analytics:
                return False
            
            export_data = {
                'analytics': analytics.dict(),
                'events': [event.dict() for event in events],
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
            import json
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error exporting negotiation data: {e}")
            return False
