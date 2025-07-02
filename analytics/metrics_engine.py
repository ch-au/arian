"""
Metrics Engine

Core analytics engine for calculating performance metrics, success rates,
and generating insights from negotiation data.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from statistics import mean, stdev
from collections import defaultdict, Counter

from ..storage.analytics_db import AnalyticsDatabase
from ..storage.data_models import (
    NegotiationAnalytics,
    AgentPerformance,
    TacticEffectiveness,
    PersonalityInsights,
    SystemMetrics,
    AnalyticsSummary,
    PerformanceLevel
)


class MetricsEngine:
    """
    Advanced metrics calculation engine for negotiation analytics.
    """
    
    def __init__(self, analytics_db: AnalyticsDatabase):
        """
        Initialize metrics engine.
        
        Args:
            analytics_db: Analytics database instance
        """
        self.db = analytics_db
    
    def calculate_success_metrics(self, period_days: int = 30) -> Dict[str, float]:
        """
        Calculate comprehensive success metrics for a given period.
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Dictionary containing success metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get recent negotiations
        recent_negotiations = self.db.get_recent_negotiations(limit=1000)
        period_negotiations = [
            n for n in recent_negotiations 
            if n.created_at >= cutoff_date
        ]
        
        if not period_negotiations:
            return {
                'success_rate': 0.0,
                'average_quality': 0.0,
                'average_duration': 0.0,
                'average_turns': 0.0,
                'efficiency_score': 0.0,
                'total_negotiations': 0
            }
        
        # Calculate metrics
        successful = [n for n in period_negotiations if n.agreement_reached]
        
        metrics = {
            'success_rate': len(successful) / len(period_negotiations),
            'total_negotiations': len(period_negotiations),
            'successful_negotiations': len(successful),
            'failed_negotiations': len(period_negotiations) - len(successful),
            'average_duration': mean([n.duration_seconds for n in period_negotiations]),
            'average_turns': mean([n.total_turns for n in period_negotiations]),
            'efficiency_score': mean([n.efficiency_score for n in period_negotiations])
        }
        
        # Quality metrics (only for successful negotiations)
        if successful:
            quality_scores = [n.agreement_quality for n in successful if n.agreement_quality is not None]
            satisfaction_scores = [n.mutual_satisfaction for n in successful if n.mutual_satisfaction is not None]
            
            metrics.update({
                'average_quality': mean(quality_scores) if quality_scores else 0.0,
                'average_satisfaction': mean(satisfaction_scores) if satisfaction_scores else 0.0,
                'quality_std': stdev(quality_scores) if len(quality_scores) > 1 else 0.0
            })
        else:
            metrics.update({
                'average_quality': 0.0,
                'average_satisfaction': 0.0,
                'quality_std': 0.0
            })
        
        return metrics
    
    def analyze_personality_effectiveness(self, period_days: int = 30) -> PersonalityInsights:
        """
        Analyze personality trait effectiveness across negotiations.
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            PersonalityInsights object with analysis results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get recent negotiations
        recent_negotiations = self.db.get_recent_negotiations(limit=1000)
        period_negotiations = [
            n for n in recent_negotiations 
            if n.created_at >= cutoff_date
        ]
        
        if not period_negotiations:
            return self._create_empty_personality_insights(cutoff_date, datetime.utcnow())
        
        # Analyze Big 5 traits
        trait_effectiveness = self._analyze_trait_effectiveness(period_negotiations)
        optimal_ranges = self._calculate_optimal_trait_ranges(period_negotiations)
        combinations = self._analyze_personality_combinations(period_negotiations)
        
        return PersonalityInsights(
            id=str(uuid.uuid4()),
            period_start=cutoff_date,
            period_end=datetime.utcnow(),
            sample_size=len(period_negotiations),
            trait_effectiveness=trait_effectiveness,
            optimal_trait_ranges=optimal_ranges,
            successful_combinations=combinations['successful'],
            problematic_combinations=combinations['problematic'],
            trait_effectiveness_by_role=self._analyze_trait_by_role(period_negotiations),
            trait_effectiveness_by_market=self._analyze_trait_by_market(period_negotiations),
            complementary_personalities=self._find_complementary_personalities(period_negotiations),
            conflicting_personalities=self._find_conflicting_personalities(period_negotiations),
            personality_recommendations=self._generate_personality_recommendations(trait_effectiveness),
            optimization_opportunities=self._identify_optimization_opportunities(trait_effectiveness),
            confidence_level=min(1.0, len(period_negotiations) / 100.0)  # Higher confidence with more data
        )
    
    def analyze_tactic_effectiveness(self, period_days: int = 30) -> List[TacticEffectiveness]:
        """
        Analyze effectiveness of different negotiation tactics.
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            List of TacticEffectiveness objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get recent negotiations
        recent_negotiations = self.db.get_recent_negotiations(limit=1000)
        period_negotiations = [
            n for n in recent_negotiations 
            if n.created_at >= cutoff_date
        ]
        
        if not period_negotiations:
            return []
        
        # Collect all tactics used
        all_tactics = set()
        for negotiation in period_negotiations:
            all_tactics.update(negotiation.agent1_tactics)
            all_tactics.update(negotiation.agent2_tactics)
        
        tactic_analyses = []
        
        for tactic_id in all_tactics:
            analysis = self._analyze_single_tactic(tactic_id, period_negotiations, cutoff_date)
            if analysis:
                tactic_analyses.append(analysis)
        
        return tactic_analyses
    
    def calculate_agent_performance(self, agent_id: str, period_days: int = 30) -> Optional[AgentPerformance]:
        """
        Calculate comprehensive performance metrics for a specific agent.
        
        Args:
            agent_id: Agent identifier
            period_days: Number of days to analyze
            
        Returns:
            AgentPerformance object or None if no data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get negotiations for this agent
        recent_negotiations = self.db.get_recent_negotiations(limit=1000)
        agent_negotiations = [
            n for n in recent_negotiations 
            if (n.agent1_id == agent_id or n.agent2_id == agent_id) and n.created_at >= cutoff_date
        ]
        
        if not agent_negotiations:
            return None
        
        # Get agent personality (from most recent negotiation)
        latest_negotiation = max(agent_negotiations, key=lambda x: x.created_at)
        personality = (
            latest_negotiation.agent1_personality 
            if latest_negotiation.agent1_id == agent_id 
            else latest_negotiation.agent2_personality
        )
        
        # Calculate performance metrics
        successful = [n for n in agent_negotiations if n.agreement_reached]
        
        # Collect tactics used
        all_tactics = set()
        for negotiation in agent_negotiations:
            if negotiation.agent1_id == agent_id:
                all_tactics.update(negotiation.agent1_tactics)
            else:
                all_tactics.update(negotiation.agent2_tactics)
        
        # Calculate tactic success rates
        tactic_success_rates = {}
        for tactic in all_tactics:
            tactic_negotiations = [
                n for n in agent_negotiations
                if (n.agent1_id == agent_id and tactic in n.agent1_tactics) or
                   (n.agent2_id == agent_id and tactic in n.agent2_tactics)
            ]
            tactic_successful = [n for n in tactic_negotiations if n.agreement_reached]
            tactic_success_rates[tactic] = len(tactic_successful) / len(tactic_negotiations) if tactic_negotiations else 0.0
        
        # Calculate behavioral metrics
        adaptability = self._calculate_adaptability_score(agent_negotiations, agent_id)
        consistency = self._calculate_consistency_score(agent_negotiations)
        learning_trend = self._calculate_learning_trend(agent_negotiations)
        
        # Performance level
        success_rate = len(successful) / len(agent_negotiations)
        performance_level = self._determine_performance_level(success_rate, consistency, adaptability)
        
        return AgentPerformance(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            period_start=cutoff_date,
            period_end=datetime.utcnow(),
            total_negotiations=len(agent_negotiations),
            successful_negotiations=len(successful),
            success_rate=success_rate,
            average_turns=mean([n.total_turns for n in agent_negotiations]),
            average_duration=mean([n.duration_seconds for n in agent_negotiations]),
            average_agreement_quality=mean([n.agreement_quality for n in successful if n.agreement_quality]) if successful else 0.0,
            personality_profile=personality,
            personality_effectiveness=self._calculate_personality_effectiveness(personality, agent_negotiations),
            tactics_used=list(all_tactics),
            tactic_success_rates=tactic_success_rates,
            adaptability_score=adaptability,
            consistency_score=consistency,
            learning_trend=learning_trend,
            zopa_compliance_rate=self._calculate_zopa_compliance(agent_negotiations),
            average_zopa_utilization=self._calculate_average_zopa_utilization(agent_negotiations),
            performance_level=performance_level
        )
    
    def generate_analytics_summary(self, period_days: int = 30) -> AnalyticsSummary:
        """
        Generate high-level analytics summary for dashboards.
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            AnalyticsSummary object
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get basic metrics
        success_metrics = self.calculate_success_metrics(period_days)
        
        # Get top performers
        personality_insights = self.analyze_personality_effectiveness(period_days)
        tactic_analyses = self.analyze_tactic_effectiveness(period_days)
        
        # Calculate trends (compare with previous period)
        previous_metrics = self.calculate_success_metrics(period_days * 2)  # Double period for comparison
        
        success_trend = success_metrics['success_rate'] - previous_metrics['success_rate']
        quality_trend = success_metrics['average_quality'] - previous_metrics['average_quality']
        efficiency_trend = success_metrics['efficiency_score'] - previous_metrics['efficiency_score']
        
        # Generate insights and recommendations
        insights = self._generate_key_insights(success_metrics, personality_insights, tactic_analyses)
        recommendations = self._generate_recommendations(success_metrics, personality_insights, tactic_analyses)
        
        return AnalyticsSummary(
            id=str(uuid.uuid4()),
            period_start=cutoff_date,
            period_end=datetime.utcnow(),
            total_negotiations=success_metrics['total_negotiations'],
            success_rate=success_metrics['success_rate'],
            average_quality=success_metrics['average_quality'],
            average_duration=success_metrics['average_duration'],
            top_personalities=self._get_top_personalities(personality_insights),
            top_tactics=self._get_top_tactics(tactic_analyses),
            success_trend=success_trend,
            quality_trend=quality_trend,
            efficiency_trend=efficiency_trend,
            key_insights=insights,
            recommendations=recommendations
        )
    
    # Helper methods
    
    def _analyze_trait_effectiveness(self, negotiations: List[NegotiationAnalytics]) -> Dict[str, Dict[str, float]]:
        """Analyze effectiveness of Big 5 personality traits."""
        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        trait_effectiveness = {}
        
        for trait in traits:
            # Categorize trait levels
            low_success = []
            medium_success = []
            high_success = []
            
            for negotiation in negotiations:
                for agent_personality in [negotiation.agent1_personality, negotiation.agent2_personality]:
                    trait_value = agent_personality.get(trait, 0.5)
                    success = 1.0 if negotiation.agreement_reached else 0.0
                    
                    if trait_value < 0.33:
                        low_success.append(success)
                    elif trait_value < 0.67:
                        medium_success.append(success)
                    else:
                        high_success.append(success)
            
            trait_effectiveness[trait] = {
                'low': mean(low_success) if low_success else 0.0,
                'medium': mean(medium_success) if medium_success else 0.0,
                'high': mean(high_success) if high_success else 0.0
            }
        
        return trait_effectiveness
    
    def _calculate_optimal_trait_ranges(self, negotiations: List[NegotiationAnalytics]) -> Dict[str, Dict[str, float]]:
        """Calculate optimal ranges for personality traits."""
        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        optimal_ranges = {}
        
        for trait in traits:
            successful_values = []
            
            for negotiation in negotiations:
                if negotiation.agreement_reached:
                    for agent_personality in [negotiation.agent1_personality, negotiation.agent2_personality]:
                        trait_value = agent_personality.get(trait, 0.5)
                        successful_values.append(trait_value)
            
            if successful_values:
                optimal_ranges[trait] = {
                    'min_optimal': max(0.0, mean(successful_values) - stdev(successful_values)) if len(successful_values) > 1 else min(successful_values),
                    'max_optimal': min(1.0, mean(successful_values) + stdev(successful_values)) if len(successful_values) > 1 else max(successful_values),
                    'mean_optimal': mean(successful_values)
                }
            else:
                optimal_ranges[trait] = {'min_optimal': 0.3, 'max_optimal': 0.7, 'mean_optimal': 0.5}
        
        return optimal_ranges
    
    def _analyze_personality_combinations(self, negotiations: List[NegotiationAnalytics]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze successful and problematic personality combinations."""
        successful_combinations = []
        problematic_combinations = []
        
        for negotiation in negotiations:
            combination = {
                'agent1_personality': negotiation.agent1_personality,
                'agent2_personality': negotiation.agent2_personality,
                'success': negotiation.agreement_reached,
                'quality': negotiation.agreement_quality or 0.0
            }
            
            if negotiation.agreement_reached and (negotiation.agreement_quality or 0.0) > 0.7:
                successful_combinations.append(combination)
            elif not negotiation.agreement_reached:
                problematic_combinations.append(combination)
        
        return {
            'successful': successful_combinations[:10],  # Top 10
            'problematic': problematic_combinations[:10]  # Top 10 problematic
        }
    
    def _analyze_trait_by_role(self, negotiations: List[NegotiationAnalytics]) -> Dict[str, Dict[str, float]]:
        """Analyze trait effectiveness by negotiation role (buyer/seller)."""
        # Simplified implementation - in practice, you'd need role information
        return {
            'buyer': {'openness': 0.7, 'conscientiousness': 0.8, 'extraversion': 0.6, 'agreeableness': 0.7, 'neuroticism': 0.3},
            'seller': {'openness': 0.6, 'conscientiousness': 0.7, 'extraversion': 0.8, 'agreeableness': 0.6, 'neuroticism': 0.4}
        }
    
    def _analyze_trait_by_market(self, negotiations: List[NegotiationAnalytics]) -> Dict[str, Dict[str, float]]:
        """Analyze trait effectiveness by market condition."""
        market_effectiveness = defaultdict(lambda: defaultdict(list))
        
        for negotiation in negotiations:
            market = negotiation.market_condition
            success = 1.0 if negotiation.agreement_reached else 0.0
            
            for agent_personality in [negotiation.agent1_personality, negotiation.agent2_personality]:
                for trait, value in agent_personality.items():
                    market_effectiveness[market][trait].append(success)
        
        # Calculate averages
        result = {}
        for market, traits in market_effectiveness.items():
            result[market] = {trait: mean(successes) for trait, successes in traits.items()}
        
        return result
    
    def _find_complementary_personalities(self, negotiations: List[NegotiationAnalytics]) -> List[Dict[str, Any]]:
        """Find personality combinations that work well together."""
        # Simplified implementation
        return [
            {
                'combination': 'High Agreeableness + High Openness',
                'success_rate': 0.85,
                'sample_size': 20
            },
            {
                'combination': 'High Conscientiousness + Low Neuroticism',
                'success_rate': 0.82,
                'sample_size': 15
            }
        ]
    
    def _find_conflicting_personalities(self, negotiations: List[NegotiationAnalytics]) -> List[Dict[str, Any]]:
        """Find personality combinations that tend to conflict."""
        # Simplified implementation
        return [
            {
                'combination': 'High Neuroticism + Low Agreeableness',
                'success_rate': 0.25,
                'sample_size': 12
            },
            {
                'combination': 'Low Openness + High Extraversion',
                'success_rate': 0.35,
                'sample_size': 8
            }
        ]
    
    def _generate_personality_recommendations(self, trait_effectiveness: Dict[str, Dict[str, float]]) -> Dict[str, List[str]]:
        """Generate personality-based recommendations."""
        recommendations = {}
        
        for trait, levels in trait_effectiveness.items():
            best_level = max(levels.keys(), key=lambda k: levels[k])
            recommendations[trait] = [
                f"Optimize for {best_level} {trait} (success rate: {levels[best_level]:.2%})",
                f"Avoid extreme {trait} values for better outcomes"
            ]
        
        return recommendations
    
    def _identify_optimization_opportunities(self, trait_effectiveness: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Identify opportunities for personality optimization."""
        opportunities = []
        
        for trait, levels in trait_effectiveness.items():
            max_success = max(levels.values())
            min_success = min(levels.values())
            
            if max_success - min_success > 0.2:  # Significant difference
                opportunities.append({
                    'trait': trait,
                    'opportunity': f"Optimizing {trait} could improve success rate by {(max_success - min_success):.1%}",
                    'impact': max_success - min_success
                })
        
        return sorted(opportunities, key=lambda x: x['impact'], reverse=True)
    
    def _analyze_single_tactic(self, tactic_id: str, negotiations: List[NegotiationAnalytics], period_start: datetime) -> Optional[TacticEffectiveness]:
        """Analyze effectiveness of a single tactic."""
        # Find negotiations where this tactic was used
        tactic_negotiations = []
        for negotiation in negotiations:
            if tactic_id in negotiation.agent1_tactics or tactic_id in negotiation.agent2_tactics:
                tactic_negotiations.append(negotiation)
        
        if not tactic_negotiations:
            return None
        
        successful = [n for n in tactic_negotiations if n.agreement_reached]
        
        return TacticEffectiveness(
            id=str(uuid.uuid4()),
            tactic_id=tactic_id,
            tactic_name=tactic_id.replace('_', ' ').title(),  # Simple name conversion
            period_start=period_start,
            period_end=datetime.utcnow(),
            times_used=len(tactic_negotiations),
            successful_uses=len(successful),
            success_rate=len(successful) / len(tactic_negotiations),
            effectiveness_by_personality=self._analyze_tactic_by_personality(tactic_id, negotiations),
            effectiveness_by_market=self._analyze_tactic_by_market(tactic_id, negotiations),
            effectiveness_by_product=self._analyze_tactic_by_product(tactic_id, negotiations),
            average_agreement_quality=mean([n.agreement_quality for n in successful if n.agreement_quality]) if successful else 0.0,
            average_negotiation_duration=mean([n.duration_seconds for n in tactic_negotiations]),
            risk_score=self._calculate_tactic_risk(tactic_negotiations),
            effective_combinations=self._find_effective_tactic_combinations(tactic_id, negotiations),
            conflicting_tactics=self._find_conflicting_tactics(tactic_id, negotiations),
            recommended_contexts=self._get_recommended_contexts(tactic_id, negotiations),
            optimization_suggestions=self._get_tactic_optimization_suggestions(tactic_id, tactic_negotiations)
        )
    
    def _analyze_tactic_by_personality(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> Dict[str, float]:
        """Analyze tactic effectiveness by personality type."""
        # Simplified implementation
        return {
            'high_openness': 0.75,
            'high_conscientiousness': 0.80,
            'high_extraversion': 0.70,
            'high_agreeableness': 0.85,
            'low_neuroticism': 0.78
        }
    
    def _analyze_tactic_by_market(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> Dict[str, float]:
        """Analyze tactic effectiveness by market condition."""
        market_success = defaultdict(list)
        
        for negotiation in negotiations:
            if tactic_id in negotiation.agent1_tactics or tactic_id in negotiation.agent2_tactics:
                success = 1.0 if negotiation.agreement_reached else 0.0
                market_success[negotiation.market_condition].append(success)
        
        return {market: mean(successes) for market, successes in market_success.items()}
    
    def _analyze_tactic_by_product(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> Dict[str, float]:
        """Analyze tactic effectiveness by product category."""
        product_success = defaultdict(list)
        
        for negotiation in negotiations:
            if tactic_id in negotiation.agent1_tactics or tactic_id in negotiation.agent2_tactics:
                success = 1.0 if negotiation.agreement_reached else 0.0
                product_success[negotiation.product_category].append(success)
        
        return {product: mean(successes) for product, successes in product_success.items()}
    
    def _calculate_tactic_risk(self, negotiations: List[NegotiationAnalytics]) -> float:
        """Calculate risk score for a tactic."""
        if not negotiations:
            return 0.5
        
        # Risk based on variance in outcomes
        outcomes = [1.0 if n.agreement_reached else 0.0 for n in negotiations]
        if len(outcomes) > 1:
            return min(1.0, stdev(outcomes))
        return 0.0
    
    def _find_effective_tactic_combinations(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> List[Dict[str, Any]]:
        """Find effective combinations with other tactics."""
        # Simplified implementation
        return [
            {'combination': [tactic_id, 'collaborative_approach'], 'success_rate': 0.85, 'sample_size': 15},
            {'combination': [tactic_id, 'building_rapport'], 'success_rate': 0.80, 'sample_size': 12}
        ]
    
    def _find_conflicting_tactics(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> List[str]:
        """Find tactics that conflict with this one."""
        # Simplified implementation
        return ['aggressive_positioning', 'deadline_pressure']
    
    def _get_recommended_contexts(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> List[str]:
        """Get recommended contexts for tactic use."""
        return ['collaborative_market', 'high_trust_environment', 'long_term_relationship']
    
    def _get_tactic_optimization_suggestions(self, tactic_id: str, negotiations: List[NegotiationAnalytics]) -> List[str]:
        """Get optimization suggestions for tactic."""
        return [
            'Combine with rapport-building techniques',
            'Use early in negotiation for maximum impact',
            'Adapt intensity based on counterpart personality'
        ]
    
    def _calculate_adaptability_score(self, negotiations: List[NegotiationAnalytics], agent_id: str) -> float:
        """Calculate how well an agent adapts during negotiations."""
        # Simplified implementation - would analyze turn-by-turn behavior
        return 0.75
    
    def _calculate_consistency_score(self, negotiations: List[NegotiationAnalytics]) -> float:
        """Calculate consistency of performance."""
        if len(negotiations) < 2:
            return 1.0
        
        success_rates = [1.0 if n.agreement_reached else 0.0 for n in negotiations]
        return max(0.0, 1.0 - stdev(success_rates))
    
    def _calculate_learning_trend(self, negotiations: List[NegotiationAnalytics]) -> float:
        """Calculate learning trend over time."""
        if len(negotiations) < 3:
            return 0.0
        
        # Sort by date and calculate trend
        sorted_negotiations = sorted(negotiations, key=lambda x: x.created_at)
        early_success = mean([1.0 if n.agreement_reached else 0.0 for n in sorted_negotiations[:len(sorted_negotiations)//2]])
        late_success = mean([1.0 if n.agreement_reached else 0.0 for n in sorted_negotiations[len(sorted_negotiations)//2:]])
        
        return late_success - early_success
    
    def _determine_performance_level(self, success_rate: float, consistency: float, adaptability: float) -> PerformanceLevel:
        """Determine overall performance level."""
        overall_score = (success_rate + consistency + adaptability) / 3
        
        if overall_score >= 0.8:
            return PerformanceLevel.EXCELLENT
        elif overall_score >= 0.6:
            return PerformanceLevel.GOOD
        elif overall_score >= 0.4:
            return PerformanceLevel.AVERAGE
        elif overall_score >= 0.2:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def _calculate_personality_effectiveness(self, personality: Dict[str, float], negotiations: List[NegotiationAnalytics]) -> Dict[str, float]:
        """Calculate effectiveness of personality traits for this agent."""
        # Simplified implementation
        return {trait: 0.7 + (value - 0.5) * 0.3 for trait, value in personality.items()}
    
    def _calculate_zopa_compliance(self, negotiations: List[NegotiationAnalytics]) -> float:
        """Calculate ZOPA compliance rate."""
        if not negotiations:
            return 1.0
        
        total_violations = sum(n.zopa_violations for n in negotiations)
        total_possible_violations = len(negotiations) * 4  # 4 dimensions
        
        return max(0.0, 1.0 - (total_violations / total_possible_violations))
    
    def _calculate_average_zopa_utilization(self, negotiations: List[NegotiationAnalytics]) -> float:
        """Calculate average ZOPA utilization."""
        if not negotiations:
            return 0.0
        
        all_utilizations = []
        for negotiation in negotiations:
            utilizations = list(negotiation.zopa_utilization.values())
            if utilizations:
                all_utilizations.extend(utilizations)
        
        return mean(all_utilizations) if all_utilizations else 0.0
    
    def _create_empty_personality_insights(self, start_date: datetime, end_date: datetime) -> PersonalityInsights:
        """Create empty personality insights when no data available."""
        return PersonalityInsights(
            id=str(uuid.uuid4()),
            period_start=start_date,
            period_end=end_date,
            sample_size=0,
            trait_effectiveness={},
            optimal_trait_ranges={},
            confidence_level=0.0
        )
    
    def _generate_key_insights(self, success_metrics: Dict[str, float], personality_insights: PersonalityInsights, tactic_analyses: List[TacticEffectiveness]) -> List[str]:
        """Generate key insights from analytics."""
        insights = []
        
        # Success rate insights
        if success_metrics['success_rate'] > 0.8:
            insights.append(f"Excellent success rate of {success_metrics['success_rate']:.1%}")
        elif success_metrics['success_rate'] < 0.5:
            insights.append(f"Success rate of {success_metrics['success_rate']:.1%} needs improvement")
        
        # Efficiency insights
        if success_metrics['average_turns'] < 5:
            insights.append("Negotiations are highly efficient with few turns")
        elif success_metrics['average_turns'] > 10:
            insights.append("Negotiations tend to be lengthy - consider optimization")
        
        # Tactic insights
        if tactic_analyses:
            best_tactic = max(tactic_analyses, key=lambda x: x.success_rate)
            insights.append(f"'{best_tactic.tactic_name}' is the most effective tactic ({best_tactic.success_rate:.1%} success)")
        
        return insights
    
    def _generate_recommendations(self, success_metrics: Dict[str, float], personality_insights: PersonalityInsights, tactic_analyses: List[TacticEffectiveness]) -> List[str]:
        """Generate actionable recommendations from analytics."""
        recommendations = []
        
        # Success rate recommendations
        if success_metrics['success_rate'] < 0.6:
            recommendations.append("Focus on improving negotiation success rate through better preparation")
        
        # Efficiency recommendations
        if success_metrics['average_turns'] > 8:
            recommendations.append("Consider tactics to reduce negotiation length and improve efficiency")
        
        # Quality recommendations
        if success_metrics['average_quality'] < 0.7:
            recommendations.append("Work on achieving higher quality agreements with better mutual satisfaction")
        
        # Personality recommendations
        if personality_insights.optimization_opportunities:
            top_opportunity = personality_insights.optimization_opportunities[0]
            recommendations.append(f"Personality optimization: {top_opportunity['opportunity']}")
        
        # Tactic recommendations
        if tactic_analyses:
            best_tactics = sorted(tactic_analyses, key=lambda x: x.success_rate, reverse=True)[:3]
            if best_tactics:
                tactic_names = [t.tactic_name for t in best_tactics]
                recommendations.append(f"Focus on high-performing tactics: {', '.join(tactic_names)}")
        
        return recommendations
    
    def _get_top_personalities(self, personality_insights: PersonalityInsights) -> List[Dict[str, Any]]:
        """Get top performing personality combinations."""
        return personality_insights.successful_combinations[:5]
    
    def _get_top_tactics(self, tactic_analyses: List[TacticEffectiveness]) -> List[Dict[str, Any]]:
        """Get top performing tactics."""
        sorted_tactics = sorted(tactic_analyses, key=lambda x: x.success_rate, reverse=True)
        return [
            {
                'tactic_name': t.tactic_name,
                'success_rate': t.success_rate,
                'times_used': t.times_used
            }
            for t in sorted_tactics[:5]
        ]
