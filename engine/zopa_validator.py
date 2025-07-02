"""
ZOPA Validator

This module provides validation and analysis of offers against ZOPA boundaries,
ensuring negotiations stay within acceptable ranges.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging

from ..models.negotiation import (
    NegotiationOffer,
    NegotiationDimension,
    NegotiationState
)
from ..models.zopa import ZOPAAnalysis, ZOPAOverlap, ZOPABoundary

logger = logging.getLogger(__name__)


class ZOPAValidationResult:
    """Result of ZOPA validation for an offer."""
    
    def __init__(self):
        self.is_valid = True
        self.violations = []
        self.warnings = []
        self.compliance_score = 1.0
        self.dimension_analysis = {}
    
    def add_violation(self, dimension: str, message: str):
        """Add a ZOPA violation."""
        self.violations.append(f"{dimension}: {message}")
        self.is_valid = False
    
    def add_warning(self, dimension: str, message: str):
        """Add a ZOPA warning."""
        self.warnings.append(f"{dimension}: {message}")
    
    def calculate_compliance_score(self):
        """Calculate overall compliance score (0-1)."""
        if not self.dimension_analysis:
            return 0.0
        
        scores = [analysis.get('compliance_score', 0.0) for analysis in self.dimension_analysis.values()]
        self.compliance_score = sum(scores) / len(scores) if scores else 0.0
        return self.compliance_score


class ZOPAValidator:
    """
    Validates offers against ZOPA boundaries and provides analysis.
    
    Ensures that negotiation offers respect the Zone of Possible Agreement
    and provides detailed feedback on compliance and violations.
    """
    
    def __init__(self):
        """Initialize the ZOPA validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_offer(
        self,
        offer: NegotiationOffer,
        dimensions: List[NegotiationDimension]
    ) -> Dict[str, bool]:
        """
        Validate an offer against ZOPA boundaries.
        
        Args:
            offer: The negotiation offer to validate
            dimensions: List of negotiation dimensions with ZOPA boundaries
            
        Returns:
            Dictionary mapping dimension names to compliance status
        """
        compliance = {}
        offer_values = offer.to_dict()
        
        for dimension in dimensions:
            dimension_name = dimension.name.value
            
            if dimension_name in offer_values:
                value = offer_values[dimension_name]
                
                # Determine which agent made the offer and check against other agent's ZOPA
                other_agent_id = "agent2" if offer.agent_id.endswith("1") else "agent1"
                
                try:
                    is_compliant = dimension.is_value_acceptable_to_agent(value, other_agent_id)
                    compliance[dimension_name] = is_compliant
                    
                    if not is_compliant:
                        self.logger.debug(f"ZOPA violation in {dimension_name}: {value} not acceptable to {other_agent_id}")
                
                except Exception as e:
                    self.logger.error(f"Error validating {dimension_name}: {e}")
                    compliance[dimension_name] = False
            else:
                compliance[dimension_name] = False
        
        return compliance
    
    def validate_offer_detailed(
        self,
        offer: NegotiationOffer,
        dimensions: List[NegotiationDimension]
    ) -> ZOPAValidationResult:
        """
        Perform detailed ZOPA validation with comprehensive analysis.
        
        Args:
            offer: The negotiation offer to validate
            dimensions: List of negotiation dimensions with ZOPA boundaries
            
        Returns:
            Detailed validation result
        """
        result = ZOPAValidationResult()
        offer_values = offer.to_dict()
        
        for dimension in dimensions:
            dimension_name = dimension.name.value
            
            if dimension_name not in offer_values:
                result.add_violation(dimension_name, "Missing value in offer")
                continue
            
            value = offer_values[dimension_name]
            analysis = self._analyze_dimension_compliance(offer, dimension, value)
            result.dimension_analysis[dimension_name] = analysis
            
            # Check for violations
            if not analysis['is_compliant']:
                result.add_violation(dimension_name, analysis['violation_message'])
            
            # Check for warnings
            if analysis.get('warning_message'):
                result.add_warning(dimension_name, analysis['warning_message'])
        
        result.calculate_compliance_score()
        return result
    
    def _analyze_dimension_compliance(
        self,
        offer: NegotiationOffer,
        dimension: NegotiationDimension,
        value: float
    ) -> Dict[str, Any]:
        """Analyze compliance for a single dimension."""
        analysis = {
            'value': value,
            'is_compliant': False,
            'compliance_score': 0.0,
            'violation_message': None,
            'warning_message': None,
            'distance_from_boundary': None,
            'position_in_range': None
        }
        
        # Determine which agent made the offer
        if offer.agent_id.endswith("1") or "agent1" in offer.agent_id:
            offering_agent = "agent1"
            receiving_agent = "agent2"
            receiving_min = dimension.agent2_min
            receiving_max = dimension.agent2_max
        else:
            offering_agent = "agent2"
            receiving_agent = "agent1"
            receiving_min = dimension.agent1_min
            receiving_max = dimension.agent1_max
        
        # Check compliance
        analysis['is_compliant'] = receiving_min <= value <= receiving_max
        
        if analysis['is_compliant']:
            # Calculate position within acceptable range
            range_size = receiving_max - receiving_min
            if range_size > 0:
                position = (value - receiving_min) / range_size
                analysis['position_in_range'] = position
                analysis['compliance_score'] = 1.0
                
                # Add warnings for edge cases
                if position < 0.1:
                    analysis['warning_message'] = f"Very close to minimum acceptable value ({receiving_min})"
                elif position > 0.9:
                    analysis['warning_message'] = f"Very close to maximum acceptable value ({receiving_max})"
            else:
                analysis['compliance_score'] = 1.0
        else:
            # Calculate how far outside the acceptable range
            if value < receiving_min:
                analysis['distance_from_boundary'] = receiving_min - value
                analysis['violation_message'] = f"Below minimum acceptable value ({receiving_min})"
            else:
                analysis['distance_from_boundary'] = value - receiving_max
                analysis['violation_message'] = f"Above maximum acceptable value ({receiving_max})"
            
            # Calculate partial compliance score based on distance
            max_distance = max(abs(receiving_min), abs(receiving_max))
            if max_distance > 0:
                distance_ratio = analysis['distance_from_boundary'] / max_distance
                analysis['compliance_score'] = max(0.0, 1.0 - distance_ratio)
        
        return analysis
    
    def get_zopa_recommendations(
        self,
        offer: NegotiationOffer,
        dimensions: List[NegotiationDimension]
    ) -> Dict[str, Any]:
        """
        Get recommendations for bringing an offer into ZOPA compliance.
        
        Args:
            offer: The negotiation offer to analyze
            dimensions: List of negotiation dimensions
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            'adjustments_needed': [],
            'concession_opportunities': [],
            'strategic_advice': [],
            'risk_assessment': 'low'
        }
        
        validation_result = self.validate_offer_detailed(offer, dimensions)
        
        violation_count = len(validation_result.violations)
        
        if violation_count == 0:
            recommendations['strategic_advice'].append("Offer is ZOPA compliant - good negotiating position")
        else:
            recommendations['risk_assessment'] = 'high' if violation_count > 2 else 'medium'
            
            for dimension_name, analysis in validation_result.dimension_analysis.items():
                if not analysis['is_compliant']:
                    # Suggest specific adjustments
                    dimension = next(d for d in dimensions if d.name.value == dimension_name)
                    
                    if offer.agent_id.endswith("1") or "agent1" in offer.agent_id:
                        target_min = dimension.agent2_min
                        target_max = dimension.agent2_max
                    else:
                        target_min = dimension.agent1_min
                        target_max = dimension.agent1_max
                    
                    current_value = analysis['value']
                    
                    if current_value < target_min:
                        recommended_value = target_min + (target_max - target_min) * 0.1  # 10% into range
                        recommendations['adjustments_needed'].append({
                            'dimension': dimension_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'reason': f"Increase to at least {target_min}"
                        })
                    else:
                        recommended_value = target_max - (target_max - target_min) * 0.1  # 10% from top
                        recommendations['adjustments_needed'].append({
                            'dimension': dimension_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'reason': f"Decrease to at most {target_max}"
                        })
                
                elif analysis.get('warning_message'):
                    # Suggest strategic improvements for compliant but risky values
                    recommendations['concession_opportunities'].append({
                        'dimension': dimension_name,
                        'current_value': analysis['value'],
                        'suggestion': analysis['warning_message']
                    })
        
        # Add strategic advice based on overall compliance
        if validation_result.compliance_score > 0.8:
            recommendations['strategic_advice'].append("Strong ZOPA compliance - consider holding position")
        elif validation_result.compliance_score > 0.5:
            recommendations['strategic_advice'].append("Moderate compliance - minor adjustments recommended")
        else:
            recommendations['strategic_advice'].append("Poor compliance - significant changes needed")
        
        return recommendations
    
    def analyze_zopa_evolution(
        self,
        negotiation: NegotiationState
    ) -> Dict[str, Any]:
        """
        Analyze how ZOPA compliance has evolved throughout the negotiation.
        
        Args:
            negotiation: The negotiation state to analyze
            
        Returns:
            Dictionary with evolution analysis
        """
        evolution = {
            'compliance_trend': [],
            'violation_patterns': {},
            'convergence_analysis': {},
            'recommendations': []
        }
        
        if not negotiation.offers:
            return evolution
        
        # Analyze compliance over time
        for offer in negotiation.offers:
            compliance = self.validate_offer(offer, negotiation.dimensions)
            compliance_score = sum(compliance.values()) / len(compliance) if compliance else 0.0
            
            evolution['compliance_trend'].append({
                'turn_number': offer.turn_number,
                'agent_id': offer.agent_id,
                'compliance_score': compliance_score,
                'violations': [dim for dim, compliant in compliance.items() if not compliant]
            })
        
        # Analyze violation patterns
        for dimension in negotiation.dimensions:
            dimension_name = dimension.name.value
            violations = []
            
            for trend_point in evolution['compliance_trend']:
                if dimension_name in trend_point['violations']:
                    violations.append(trend_point['turn_number'])
            
            if violations:
                evolution['violation_patterns'][dimension_name] = {
                    'violation_turns': violations,
                    'frequency': len(violations) / len(negotiation.offers),
                    'recent_violations': any(turn > len(negotiation.offers) - 3 for turn in violations[-3:])
                }
        
        # Analyze convergence toward ZOPA compliance
        if len(evolution['compliance_trend']) >= 4:
            recent_scores = [point['compliance_score'] for point in evolution['compliance_trend'][-4:]]
            early_scores = [point['compliance_score'] for point in evolution['compliance_trend'][:4]]
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            early_avg = sum(early_scores) / len(early_scores)
            
            evolution['convergence_analysis'] = {
                'improvement': recent_avg - early_avg,
                'recent_average': recent_avg,
                'early_average': early_avg,
                'trend': 'improving' if recent_avg > early_avg else 'declining'
            }
        
        # Generate recommendations based on patterns
        if evolution['violation_patterns']:
            persistent_violations = [
                dim for dim, pattern in evolution['violation_patterns'].items()
                if pattern['frequency'] > 0.5
            ]
            
            if persistent_violations:
                evolution['recommendations'].append(
                    f"Address persistent violations in: {', '.join(persistent_violations)}"
                )
        
        if evolution.get('convergence_analysis', {}).get('trend') == 'declining':
            evolution['recommendations'].append("ZOPA compliance is declining - review negotiation strategy")
        
        return evolution
    
    def calculate_zopa_utilization(
        self,
        negotiation: NegotiationState
    ) -> Dict[str, float]:
        """
        Calculate how much of the available ZOPA space has been utilized.
        
        Args:
            negotiation: The negotiation state to analyze
            
        Returns:
            Dictionary mapping dimensions to utilization scores (0-1)
        """
        utilization = {}
        
        for dimension in negotiation.dimensions:
            if not dimension.has_overlap():
                utilization[dimension.name.value] = 0.0
                continue
            
            overlap_range = dimension.get_overlap_range()
            if not overlap_range:
                utilization[dimension.name.value] = 0.0
                continue
            
            overlap_min, overlap_max = overlap_range
            overlap_size = overlap_max - overlap_min
            
            if overlap_size == 0:
                utilization[dimension.name.value] = 1.0  # Single point overlap
                continue
            
            # Find all values offered in this dimension
            offered_values = []
            for offer in negotiation.offers:
                offer_dict = offer.to_dict()
                if dimension.name.value in offer_dict:
                    value = offer_dict[dimension.name.value]
                    if overlap_min <= value <= overlap_max:
                        offered_values.append(value)
            
            if not offered_values:
                utilization[dimension.name.value] = 0.0
            else:
                # Calculate range of values explored within ZOPA
                explored_min = min(offered_values)
                explored_max = max(offered_values)
                explored_range = explored_max - explored_min
                
                utilization[dimension.name.value] = min(explored_range / overlap_size, 1.0)
        
        return utilization
    
    def get_optimal_offer_suggestion(
        self,
        agent_id: str,
        dimensions: List[NegotiationDimension],
        negotiation_history: Optional[List[NegotiationOffer]] = None
    ) -> Dict[str, float]:
        """
        Suggest optimal offer values that maximize ZOPA compliance.
        
        Args:
            agent_id: ID of the agent making the offer
            dimensions: List of negotiation dimensions
            negotiation_history: Previous offers for context
            
        Returns:
            Dictionary with suggested values for each dimension
        """
        suggestions = {}
        
        for dimension in dimensions:
            if not dimension.has_overlap():
                # No overlap - suggest agent's preferred value
                if agent_id.endswith("1") or "agent1" in agent_id:
                    suggestions[dimension.name.value] = dimension.agent1_max
                else:
                    suggestions[dimension.name.value] = dimension.agent2_max
                continue
            
            overlap_range = dimension.get_overlap_range()
            if not overlap_range:
                continue
            
            overlap_min, overlap_max = overlap_range
            
            # Start with midpoint of overlap
            suggested_value = (overlap_min + overlap_max) / 2
            
            # Adjust based on agent's preferences
            if agent_id.endswith("1") or "agent1" in agent_id:
                # Agent 1 prefers values closer to their max
                agent_preference = dimension.agent1_max
                if overlap_min <= agent_preference <= overlap_max:
                    suggested_value = agent_preference
                elif agent_preference > overlap_max:
                    suggested_value = overlap_max
                else:
                    suggested_value = overlap_min
            else:
                # Agent 2 prefers values closer to their max
                agent_preference = dimension.agent2_max
                if overlap_min <= agent_preference <= overlap_max:
                    suggested_value = agent_preference
                elif agent_preference > overlap_max:
                    suggested_value = overlap_max
                else:
                    suggested_value = overlap_min
            
            # Adjust based on negotiation history if available
            if negotiation_history:
                recent_offers = negotiation_history[-3:]  # Last 3 offers
                dimension_values = []
                
                for offer in recent_offers:
                    offer_dict = offer.to_dict()
                    if dimension.name.value in offer_dict:
                        dimension_values.append(offer_dict[dimension.name.value])
                
                if dimension_values:
                    # Move slightly toward the average of recent offers
                    recent_avg = sum(dimension_values) / len(dimension_values)
                    suggested_value = (suggested_value * 0.7) + (recent_avg * 0.3)
                    
                    # Ensure still within overlap
                    suggested_value = max(overlap_min, min(overlap_max, suggested_value))
            
            suggestions[dimension.name.value] = suggested_value
        
        return suggestions
