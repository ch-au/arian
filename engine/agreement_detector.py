"""
Agreement Detector

This module detects when agreements are reached in negotiations and analyzes
the quality and characteristics of those agreements.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging

from ..models.negotiation import (
    NegotiationState,
    NegotiationOffer,
    NegotiationResult,
    NegotiationStatus
)
from ..models.zopa import ZOPAAnalysis

logger = logging.getLogger(__name__)


class AgreementQuality:
    """Represents the quality assessment of a negotiation agreement."""
    
    def __init__(self):
        self.overall_score = 0.0
        self.mutual_satisfaction = 0.0
        self.zopa_compliance = 0.0
        self.efficiency_score = 0.0
        self.fairness_score = 0.0
        self.stability_score = 0.0
        self.details = {}


class AgreementDetector:
    """
    Detects and analyzes agreements in negotiations.
    
    Determines when agreements are reached, assesses their quality,
    and provides insights into the negotiation outcome.
    """
    
    def __init__(self):
        """Initialize the agreement detector."""
        self.logger = logging.getLogger(__name__)
    
    def check_for_agreement(self, negotiation: NegotiationState) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if an agreement has been reached in the negotiation.
        
        Args:
            negotiation: Current negotiation state
            
        Returns:
            Tuple of (agreement_reached, agreement_details)
        """
        if len(negotiation.offers) < 2:
            return False, None
        
        # Get latest offers from both agents
        latest_offers = negotiation.get_latest_offers()
        
        if not all(latest_offers.values()):
            return False, None
        
        offer1 = latest_offers[negotiation.agent1_id]
        offer2 = latest_offers[negotiation.agent2_id]
        
        # Check for exact match across all dimensions
        agreement_reached = (
            offer1.volume == offer2.volume and
            offer1.price == offer2.price and
            offer1.payment_terms == offer2.payment_terms and
            offer1.contract_duration == offer2.contract_duration
        )
        
        if agreement_reached:
            agreement_details = {
                'agreed_terms': offer1.to_dict(),
                'final_offers': {
                    negotiation.agent1_id: offer1.to_dict(),
                    negotiation.agent2_id: offer2.to_dict()
                },
                'agreement_turn': max(offer1.turn_number, offer2.turn_number),
                'negotiation_rounds': negotiation.current_round
            }
            
            self.logger.info(f"Agreement detected in negotiation {negotiation.id}")
            return True, agreement_details
        
        return False, None
    
    def check_for_near_agreement(
        self, 
        negotiation: NegotiationState, 
        tolerance_percentage: float = 0.05
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if agents are close to agreement within a tolerance threshold.
        
        Args:
            negotiation: Current negotiation state
            tolerance_percentage: Acceptable difference as percentage (0.05 = 5%)
            
        Returns:
            Tuple of (near_agreement, analysis)
        """
        if len(negotiation.offers) < 2:
            return False, None
        
        latest_offers = negotiation.get_latest_offers()
        
        if not all(latest_offers.values()):
            return False, None
        
        offer1 = latest_offers[negotiation.agent1_id]
        offer2 = latest_offers[negotiation.agent2_id]
        
        # Calculate differences for each dimension
        differences = {}
        within_tolerance = {}
        
        dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
        
        for dimension in dimensions:
            value1 = getattr(offer1, dimension)
            value2 = getattr(offer2, dimension)
            
            # Calculate percentage difference
            avg_value = (value1 + value2) / 2
            if avg_value > 0:
                diff_percentage = abs(value1 - value2) / avg_value
                differences[dimension] = {
                    'absolute_diff': abs(value1 - value2),
                    'percentage_diff': diff_percentage,
                    'value1': value1,
                    'value2': value2
                }
                within_tolerance[dimension] = diff_percentage <= tolerance_percentage
            else:
                differences[dimension] = {
                    'absolute_diff': 0,
                    'percentage_diff': 0,
                    'value1': value1,
                    'value2': value2
                }
                within_tolerance[dimension] = True
        
        # Check if all dimensions are within tolerance
        near_agreement = all(within_tolerance.values())
        
        analysis = {
            'near_agreement': near_agreement,
            'tolerance_used': tolerance_percentage,
            'dimensions_analysis': differences,
            'dimensions_within_tolerance': within_tolerance,
            'overall_similarity': sum(within_tolerance.values()) / len(within_tolerance)
        }
        
        if near_agreement:
            self.logger.info(f"Near agreement detected in negotiation {negotiation.id} "
                           f"(tolerance: {tolerance_percentage:.1%})")
        
        return near_agreement, analysis
    
    def assess_agreement_quality(
        self, 
        negotiation: NegotiationState,
        agreement_details: Dict[str, Any]
    ) -> AgreementQuality:
        """
        Assess the quality of a reached agreement.
        
        Args:
            negotiation: The negotiation state
            agreement_details: Details of the agreement
            
        Returns:
            Agreement quality assessment
        """
        quality = AgreementQuality()
        
        # Calculate ZOPA compliance
        quality.zopa_compliance = self._calculate_zopa_compliance(negotiation, agreement_details)
        
        # Calculate mutual satisfaction
        quality.mutual_satisfaction = self._calculate_mutual_satisfaction(negotiation, agreement_details)
        
        # Calculate efficiency (how quickly agreement was reached)
        quality.efficiency_score = self._calculate_efficiency_score(negotiation, agreement_details)
        
        # Calculate fairness (how balanced the outcome is)
        quality.fairness_score = self._calculate_fairness_score(negotiation, agreement_details)
        
        # Calculate stability (likelihood agreement will hold)
        quality.stability_score = self._calculate_stability_score(negotiation, agreement_details)
        
        # Calculate overall score
        quality.overall_score = (
            quality.zopa_compliance * 0.25 +
            quality.mutual_satisfaction * 0.25 +
            quality.efficiency_score * 0.20 +
            quality.fairness_score * 0.15 +
            quality.stability_score * 0.15
        )
        
        # Store detailed analysis
        quality.details = {
            'zopa_compliance_details': self._get_zopa_compliance_details(negotiation, agreement_details),
            'satisfaction_breakdown': self._get_satisfaction_breakdown(negotiation, agreement_details),
            'efficiency_analysis': self._get_efficiency_analysis(negotiation, agreement_details),
            'fairness_analysis': self._get_fairness_analysis(negotiation, agreement_details),
            'stability_factors': self._get_stability_factors(negotiation, agreement_details)
        }
        
        return quality
    
    def _calculate_zopa_compliance(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> float:
        """Calculate how well the agreement complies with ZOPA boundaries."""
        agreed_terms = agreement_details['agreed_terms']
        compliance_scores = []
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in agreed_terms:
                agreed_value = agreed_terms[dimension_name]
                
                # Check if value is within both agents' acceptable ranges
                agent1_acceptable = dimension.is_value_acceptable_to_agent(agreed_value, "agent1")
                agent2_acceptable = dimension.is_value_acceptable_to_agent(agreed_value, "agent2")
                
                if agent1_acceptable and agent2_acceptable:
                    compliance_scores.append(1.0)
                elif agent1_acceptable or agent2_acceptable:
                    compliance_scores.append(0.5)
                else:
                    compliance_scores.append(0.0)
        
        return sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.0
    
    def _calculate_mutual_satisfaction(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> float:
        """Calculate estimated mutual satisfaction with the agreement."""
        agreed_terms = agreement_details['agreed_terms']
        satisfaction_scores = []
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in agreed_terms:
                agreed_value = agreed_terms[dimension_name]
                
                # Calculate satisfaction for each agent
                agent1_satisfaction = self._calculate_agent_satisfaction(
                    agreed_value, dimension.agent1_min, dimension.agent1_max
                )
                agent2_satisfaction = self._calculate_agent_satisfaction(
                    agreed_value, dimension.agent2_min, dimension.agent2_max
                )
                
                # Use minimum satisfaction (weakest link)
                mutual_satisfaction = min(agent1_satisfaction, agent2_satisfaction)
                satisfaction_scores.append(mutual_satisfaction)
        
        return sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.0
    
    def _calculate_agent_satisfaction(self, value: float, min_acceptable: float, max_desired: float) -> float:
        """Calculate satisfaction score for a single agent on one dimension."""
        if value < min_acceptable or value > max_desired:
            return 0.0  # Outside acceptable range
        
        # Calculate position within acceptable range
        range_size = max_desired - min_acceptable
        if range_size == 0:
            return 1.0  # Single point preference
        
        # Assume satisfaction is highest at max_desired, lowest at min_acceptable
        satisfaction = (value - min_acceptable) / range_size
        return satisfaction
    
    def _calculate_efficiency_score(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> float:
        """Calculate how efficiently the agreement was reached."""
        rounds_used = agreement_details['negotiation_rounds']
        max_rounds = negotiation.max_rounds
        
        # Efficiency decreases as more rounds are used
        efficiency = 1.0 - (rounds_used / max_rounds)
        
        # Bonus for very quick agreements
        if rounds_used <= 3:
            efficiency += 0.2
        
        return max(0.0, min(1.0, efficiency))
    
    def _calculate_fairness_score(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> float:
        """Calculate how fair the agreement is to both parties."""
        agreed_terms = agreement_details['agreed_terms']
        fairness_scores = []
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in agreed_terms:
                agreed_value = agreed_terms[dimension_name]
                
                # Calculate how close the agreed value is to each agent's midpoint
                agent1_midpoint = (dimension.agent1_min + dimension.agent1_max) / 2
                agent2_midpoint = (dimension.agent2_min + dimension.agent2_max) / 2
                
                # Calculate distances from midpoints
                dist1 = abs(agreed_value - agent1_midpoint)
                dist2 = abs(agreed_value - agent2_midpoint)
                
                # Fairness is higher when distances are similar
                total_dist = dist1 + dist2
                if total_dist > 0:
                    fairness = 1.0 - abs(dist1 - dist2) / total_dist
                else:
                    fairness = 1.0
                
                fairness_scores.append(fairness)
        
        return sum(fairness_scores) / len(fairness_scores) if fairness_scores else 0.0
    
    def _calculate_stability_score(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> float:
        """Calculate likelihood that the agreement will be stable."""
        stability_factors = []
        
        # Factor 1: ZOPA compliance (stable if within ZOPA)
        zopa_compliance = self._calculate_zopa_compliance(negotiation, agreement_details)
        stability_factors.append(zopa_compliance)
        
        # Factor 2: Convergence pattern (stable if gradual convergence)
        convergence_stability = self._analyze_convergence_stability(negotiation)
        stability_factors.append(convergence_stability)
        
        # Factor 3: Final offer confidence
        final_confidence = self._get_final_offer_confidence(negotiation)
        stability_factors.append(final_confidence)
        
        return sum(stability_factors) / len(stability_factors)
    
    def _analyze_convergence_stability(self, negotiation: NegotiationState) -> float:
        """Analyze if the convergence pattern suggests a stable agreement."""
        if len(negotiation.offers) < 4:
            return 0.5  # Neutral score for insufficient data
        
        # Look at the last few offers to see if there was gradual convergence
        recent_offers = negotiation.offers[-4:]
        
        # Group by agent
        agent1_offers = [o for o in recent_offers if o.agent_id == negotiation.agent1_id]
        agent2_offers = [o for o in recent_offers if o.agent_id == negotiation.agent2_id]
        
        if len(agent1_offers) < 2 or len(agent2_offers) < 2:
            return 0.5
        
        # Calculate convergence for each dimension
        convergence_scores = []
        dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
        
        for dimension in dimensions:
            agent1_values = [getattr(o, dimension) for o in agent1_offers]
            agent2_values = [getattr(o, dimension) for o in agent2_offers]
            
            # Check if values are converging (getting closer)
            initial_distance = abs(agent1_values[0] - agent2_values[0])
            final_distance = abs(agent1_values[-1] - agent2_values[-1])
            
            if initial_distance > 0:
                convergence = (initial_distance - final_distance) / initial_distance
                convergence_scores.append(max(0.0, min(1.0, convergence)))
            else:
                convergence_scores.append(1.0)
        
        return sum(convergence_scores) / len(convergence_scores)
    
    def _get_final_offer_confidence(self, negotiation: NegotiationState) -> float:
        """Get the confidence level of the final offers."""
        if not negotiation.offers:
            return 0.0
        
        # Get the last two offers (one from each agent)
        recent_offers = negotiation.offers[-2:]
        confidence_scores = [offer.confidence for offer in recent_offers]
        
        return sum(confidence_scores) / len(confidence_scores)
    
    def _get_zopa_compliance_details(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed ZOPA compliance analysis."""
        agreed_terms = agreement_details['agreed_terms']
        details = {}
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in agreed_terms:
                agreed_value = agreed_terms[dimension_name]
                
                details[dimension_name] = {
                    'agreed_value': agreed_value,
                    'agent1_range': {'min': dimension.agent1_min, 'max': dimension.agent1_max},
                    'agent2_range': {'min': dimension.agent2_min, 'max': dimension.agent2_max},
                    'agent1_acceptable': dimension.is_value_acceptable_to_agent(agreed_value, "agent1"),
                    'agent2_acceptable': dimension.is_value_acceptable_to_agent(agreed_value, "agent2"),
                    'has_overlap': dimension.has_overlap(),
                    'overlap_range': dimension.get_overlap_range()
                }
        
        return details
    
    def _get_satisfaction_breakdown(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed satisfaction analysis for each agent and dimension."""
        agreed_terms = agreement_details['agreed_terms']
        breakdown = {'agent1': {}, 'agent2': {}, 'mutual': {}}
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in agreed_terms:
                agreed_value = agreed_terms[dimension_name]
                
                agent1_sat = self._calculate_agent_satisfaction(
                    agreed_value, dimension.agent1_min, dimension.agent1_max
                )
                agent2_sat = self._calculate_agent_satisfaction(
                    agreed_value, dimension.agent2_min, dimension.agent2_max
                )
                
                breakdown['agent1'][dimension_name] = agent1_sat
                breakdown['agent2'][dimension_name] = agent2_sat
                breakdown['mutual'][dimension_name] = min(agent1_sat, agent2_sat)
        
        return breakdown
    
    def _get_efficiency_analysis(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed efficiency analysis."""
        return {
            'rounds_used': agreement_details['negotiation_rounds'],
            'max_rounds': negotiation.max_rounds,
            'efficiency_ratio': 1.0 - (agreement_details['negotiation_rounds'] / negotiation.max_rounds),
            'total_turns': len(negotiation.turns),
            'offers_made': len(negotiation.offers),
            'agreement_turn': agreement_details['agreement_turn']
        }
    
    def _get_fairness_analysis(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed fairness analysis."""
        agreed_terms = agreement_details['agreed_terms']
        analysis = {}
        
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            if dimension_name in agreed_terms:
                agreed_value = agreed_terms[dimension_name]
                
                agent1_midpoint = (dimension.agent1_min + dimension.agent1_max) / 2
                agent2_midpoint = (dimension.agent2_min + dimension.agent2_max) / 2
                
                analysis[dimension_name] = {
                    'agreed_value': agreed_value,
                    'agent1_midpoint': agent1_midpoint,
                    'agent2_midpoint': agent2_midpoint,
                    'distance_from_agent1_midpoint': abs(agreed_value - agent1_midpoint),
                    'distance_from_agent2_midpoint': abs(agreed_value - agent2_midpoint),
                    'fairness_score': self._calculate_dimension_fairness(
                        agreed_value, agent1_midpoint, agent2_midpoint
                    )
                }
        
        return analysis
    
    def _calculate_dimension_fairness(self, agreed_value: float, midpoint1: float, midpoint2: float) -> float:
        """Calculate fairness score for a single dimension."""
        dist1 = abs(agreed_value - midpoint1)
        dist2 = abs(agreed_value - midpoint2)
        total_dist = dist1 + dist2
        
        if total_dist > 0:
            return 1.0 - abs(dist1 - dist2) / total_dist
        else:
            return 1.0
    
    def _get_stability_factors(self, negotiation: NegotiationState, agreement_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed stability analysis."""
        return {
            'zopa_compliance': self._calculate_zopa_compliance(negotiation, agreement_details),
            'convergence_stability': self._analyze_convergence_stability(negotiation),
            'final_offer_confidence': self._get_final_offer_confidence(negotiation),
            'negotiation_length': len(negotiation.turns),
            'offer_consistency': self._analyze_offer_consistency(negotiation)
        }
    
    def _analyze_offer_consistency(self, negotiation: NegotiationState) -> float:
        """Analyze how consistent the final offers were with earlier positions."""
        if len(negotiation.offers) < 4:
            return 0.5
        
        # Compare final offers with earlier offers from same agents
        consistency_scores = []
        
        for agent_id in [negotiation.agent1_id, negotiation.agent2_id]:
            agent_offers = [o for o in negotiation.offers if o.agent_id == agent_id]
            
            if len(agent_offers) >= 2:
                first_offer = agent_offers[0]
                last_offer = agent_offers[-1]
                
                # Calculate consistency across dimensions
                dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
                dim_consistency = []
                
                for dimension in dimensions:
                    first_value = getattr(first_offer, dimension)
                    last_value = getattr(last_offer, dimension)
                    
                    # Consistency is higher when changes are gradual
                    if first_value != 0:
                        change_ratio = abs(last_value - first_value) / abs(first_value)
                        consistency = max(0.0, 1.0 - change_ratio)
                    else:
                        consistency = 1.0 if last_value == 0 else 0.0
                    
                    dim_consistency.append(consistency)
                
                agent_consistency = sum(dim_consistency) / len(dim_consistency)
                consistency_scores.append(agent_consistency)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def generate_agreement_report(
        self, 
        negotiation: NegotiationState, 
        agreement_details: Dict[str, Any],
        quality: AgreementQuality
    ) -> Dict[str, Any]:
        """Generate a comprehensive agreement report."""
        return {
            'negotiation_id': negotiation.id,
            'agreement_summary': {
                'agreed_terms': agreement_details['agreed_terms'],
                'rounds_to_agreement': agreement_details['negotiation_rounds'],
                'total_turns': len(negotiation.turns),
                'agreement_turn': agreement_details['agreement_turn']
            },
            'quality_assessment': {
                'overall_score': quality.overall_score,
                'mutual_satisfaction': quality.mutual_satisfaction,
                'zopa_compliance': quality.zopa_compliance,
                'efficiency_score': quality.efficiency_score,
                'fairness_score': quality.fairness_score,
                'stability_score': quality.stability_score
            },
            'detailed_analysis': quality.details,
            'recommendations': self._generate_agreement_recommendations(quality),
            'success_factors': self._identify_success_factors(negotiation, quality),
            'lessons_learned': self._extract_lessons_learned(negotiation, quality)
        }
    
    def _generate_agreement_recommendations(self, quality: AgreementQuality) -> List[str]:
        """Generate recommendations based on agreement quality."""
        recommendations = []
        
        if quality.overall_score >= 0.8:
            recommendations.append("Excellent agreement - consider using similar approach in future negotiations")
        elif quality.overall_score >= 0.6:
            recommendations.append("Good agreement with room for improvement")
        else:
            recommendations.append("Agreement reached but significant improvements possible")
        
        if quality.zopa_compliance < 0.7:
            recommendations.append("Focus on better ZOPA analysis in future negotiations")
        
        if quality.efficiency_score < 0.5:
            recommendations.append("Consider more efficient negotiation strategies to reduce time to agreement")
        
        if quality.fairness_score < 0.6:
            recommendations.append("Work on achieving more balanced outcomes")
        
        if quality.stability_score < 0.7:
            recommendations.append("Pay attention to factors that ensure agreement stability")
        
        return recommendations
    
    def _identify_success_factors(self, negotiation: NegotiationState, quality: AgreementQuality) -> List[str]:
        """Identify factors that contributed to successful agreement."""
        factors = []
        
        if quality.zopa_compliance > 0.8:
            factors.append("Strong ZOPA compliance ensured mutually acceptable outcome")
        
        if quality.efficiency_score > 0.7:
            factors.append("Efficient negotiation process minimized time and effort")
        
        if quality.mutual_satisfaction > 0.7:
            factors.append("High mutual satisfaction indicates win-win outcome")
        
        if len(negotiation.offers) > 4:
            factors.append("Sufficient exploration of options led to better agreement")
        
        return factors
    
    def _extract_lessons_learned(self, negotiation: NegotiationState, quality: AgreementQuality) -> List[str]:
        """Extract lessons learned from the negotiation."""
        lessons = []
        
        if quality.overall_score < 0.5:
            lessons.append("Low overall quality suggests need for better preparation and strategy")
        
        if quality.fairness_score < quality.mutual_satisfaction:
            lessons.append("Focus on achieving more balanced outcomes even when satisfaction is high")
        
        if quality.efficiency_score < 0.4:
            lessons.append("Long negotiations may indicate need for better initial positioning")
        
        return lessons
