"""
Analytics Data Models

Pydantic models for storing and analyzing negotiation performance data,
agent effectiveness, tactic performance, and system metrics.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class AnalyticsEventType(str, Enum):
    """Types of analytics events."""
    NEGOTIATION_START = "negotiation_start"
    NEGOTIATION_END = "negotiation_end"
    TURN_COMPLETED = "turn_completed"
    AGREEMENT_REACHED = "agreement_reached"
    NEGOTIATION_FAILED = "negotiation_failed"
    ZOPA_VIOLATION = "zopa_violation"
    TACTIC_APPLIED = "tactic_applied"


class PerformanceLevel(str, Enum):
    """Performance level categories."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"


class NegotiationAnalytics(BaseModel):
    """
    Comprehensive analytics data for a completed negotiation.
    """
    id: str = Field(..., description="Unique analytics record ID")
    negotiation_id: str = Field(..., description="Original negotiation ID")
    
    # Basic negotiation info
    started_at: datetime = Field(..., description="Negotiation start time")
    ended_at: datetime = Field(..., description="Negotiation end time")
    duration_seconds: float = Field(..., description="Total negotiation duration")
    
    # Participants
    agent1_id: str = Field(..., description="First agent ID")
    agent2_id: str = Field(..., description="Second agent ID")
    agent1_personality: Dict[str, float] = Field(..., description="Agent 1 Big 5 traits")
    agent2_personality: Dict[str, float] = Field(..., description="Agent 2 Big 5 traits")
    agent1_tactics: List[str] = Field(..., description="Agent 1 selected tactics")
    agent2_tactics: List[str] = Field(..., description="Agent 2 selected tactics")
    
    # Outcome metrics
    agreement_reached: bool = Field(..., description="Whether agreement was reached")
    total_turns: int = Field(..., description="Total number of turns")
    total_rounds: int = Field(..., description="Total number of rounds")
    
    # Performance metrics
    success_score: float = Field(ge=0.0, le=1.0, description="Overall success score")
    efficiency_score: float = Field(ge=0.0, le=1.0, description="Negotiation efficiency")
    agreement_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality of final agreement")
    mutual_satisfaction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Mutual satisfaction score")
    
    # ZOPA analysis
    zopa_utilization: Dict[str, float] = Field(default_factory=dict, description="ZOPA utilization by dimension")
    zopa_violations: int = Field(default=0, description="Number of ZOPA violations")
    
    # Final agreement (if reached)
    final_agreement: Optional[Dict[str, Any]] = Field(None, description="Final agreement terms")
    
    # Context information
    product_category: str = Field(..., description="Product category")
    market_condition: str = Field(..., description="Market condition")
    baseline_values: Dict[str, float] = Field(..., description="Baseline negotiation values")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentPerformance(BaseModel):
    """
    Performance analytics for individual agents across multiple negotiations.
    """
    id: str = Field(..., description="Unique performance record ID")
    agent_id: str = Field(..., description="Agent identifier")
    
    # Time period
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    
    # Basic statistics
    total_negotiations: int = Field(..., description="Total negotiations participated in")
    successful_negotiations: int = Field(..., description="Negotiations with agreements")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate percentage")
    
    # Performance metrics
    average_turns: float = Field(..., description="Average turns per negotiation")
    average_duration: float = Field(..., description="Average negotiation duration")
    average_agreement_quality: float = Field(ge=0.0, le=1.0, description="Average agreement quality")
    
    # Personality effectiveness
    personality_profile: Dict[str, float] = Field(..., description="Agent's Big 5 personality")
    personality_effectiveness: Dict[str, float] = Field(..., description="Effectiveness by trait")
    
    # Tactic performance
    tactics_used: List[str] = Field(..., description="Tactics used by agent")
    tactic_success_rates: Dict[str, float] = Field(..., description="Success rate by tactic")
    
    # Behavioral patterns
    adaptability_score: float = Field(ge=0.0, le=1.0, description="How well agent adapts")
    consistency_score: float = Field(ge=0.0, le=1.0, description="Performance consistency")
    learning_trend: float = Field(description="Performance improvement trend")
    
    # ZOPA performance
    zopa_compliance_rate: float = Field(ge=0.0, le=1.0, description="ZOPA compliance rate")
    average_zopa_utilization: float = Field(ge=0.0, le=1.0, description="Average ZOPA utilization")
    
    # Performance level
    performance_level: PerformanceLevel = Field(..., description="Overall performance level")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TacticEffectiveness(BaseModel):
    """
    Analytics for negotiation tactic effectiveness across different contexts.
    """
    id: str = Field(..., description="Unique tactic analytics ID")
    tactic_id: str = Field(..., description="Tactic identifier")
    tactic_name: str = Field(..., description="Tactic name")
    
    # Analysis period
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    
    # Usage statistics
    times_used: int = Field(..., description="Number of times tactic was used")
    successful_uses: int = Field(..., description="Number of successful applications")
    success_rate: float = Field(ge=0.0, le=1.0, description="Overall success rate")
    
    # Context effectiveness
    effectiveness_by_personality: Dict[str, float] = Field(default_factory=dict, description="Effectiveness by personality type")
    effectiveness_by_market: Dict[str, float] = Field(default_factory=dict, description="Effectiveness by market condition")
    effectiveness_by_product: Dict[str, float] = Field(default_factory=dict, description="Effectiveness by product category")
    
    # Performance metrics
    average_agreement_quality: float = Field(ge=0.0, le=1.0, description="Average agreement quality when used")
    average_negotiation_duration: float = Field(..., description="Average duration when used")
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk associated with tactic")
    
    # Combination analysis
    effective_combinations: List[Dict[str, Any]] = Field(default_factory=list, description="Effective tactic combinations")
    conflicting_tactics: List[str] = Field(default_factory=list, description="Tactics that conflict with this one")
    
    # Recommendations
    recommended_contexts: List[str] = Field(default_factory=list, description="Contexts where tactic is recommended")
    optimization_suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PersonalityInsights(BaseModel):
    """
    Analytics insights about personality trait effectiveness in negotiations.
    """
    id: str = Field(..., description="Unique insight record ID")
    
    # Analysis scope
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    sample_size: int = Field(..., description="Number of negotiations analyzed")
    
    # Big 5 trait analysis
    trait_effectiveness: Dict[str, Dict[str, float]] = Field(..., description="Effectiveness by trait level")
    optimal_trait_ranges: Dict[str, Dict[str, float]] = Field(..., description="Optimal ranges for each trait")
    
    # Personality combinations
    successful_combinations: List[Dict[str, Any]] = Field(default_factory=list, description="Most successful personality combinations")
    problematic_combinations: List[Dict[str, Any]] = Field(default_factory=list, description="Problematic personality combinations")
    
    # Context-dependent insights
    trait_effectiveness_by_role: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Effectiveness by negotiation role")
    trait_effectiveness_by_market: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Effectiveness by market condition")
    
    # Interaction patterns
    complementary_personalities: List[Dict[str, Any]] = Field(default_factory=list, description="Personalities that work well together")
    conflicting_personalities: List[Dict[str, Any]] = Field(default_factory=list, description="Personalities that conflict")
    
    # Recommendations
    personality_recommendations: Dict[str, List[str]] = Field(default_factory=dict, description="Recommendations by context")
    optimization_opportunities: List[Dict[str, Any]] = Field(default_factory=list, description="Opportunities for improvement")
    
    # Statistical confidence
    confidence_level: float = Field(ge=0.0, le=1.0, description="Statistical confidence in insights")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemMetrics(BaseModel):
    """
    System performance and operational metrics.
    """
    id: str = Field(..., description="Unique metrics record ID")
    
    # Time period
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    
    # Negotiation throughput
    total_negotiations: int = Field(..., description="Total negotiations in period")
    successful_negotiations: int = Field(..., description="Successful negotiations")
    failed_negotiations: int = Field(..., description="Failed negotiations")
    negotiations_per_hour: float = Field(..., description="Average negotiations per hour")
    
    # Performance metrics
    average_response_time: float = Field(..., description="Average response time per turn")
    average_negotiation_duration: float = Field(..., description="Average negotiation duration")
    api_call_efficiency: float = Field(ge=0.0, le=1.0, description="OpenAI API efficiency score")
    
    # Resource usage
    cpu_usage_avg: float = Field(ge=0.0, le=100.0, description="Average CPU usage percentage")
    memory_usage_avg: float = Field(..., description="Average memory usage in MB")
    storage_usage: float = Field(..., description="Storage usage in MB")
    
    # Error tracking
    error_rate: float = Field(ge=0.0, le=1.0, description="Error rate percentage")
    timeout_rate: float = Field(ge=0.0, le=1.0, description="Timeout rate percentage")
    api_error_rate: float = Field(ge=0.0, le=1.0, description="API error rate percentage")
    
    # Quality metrics
    average_agreement_quality: float = Field(ge=0.0, le=1.0, description="Average agreement quality")
    user_satisfaction_score: float = Field(ge=0.0, le=1.0, description="User satisfaction score")
    
    # Alerts and issues
    critical_alerts: int = Field(default=0, description="Number of critical alerts")
    performance_warnings: int = Field(default=0, description="Number of performance warnings")
    
    # Metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsEvent(BaseModel):
    """
    Individual analytics event for real-time tracking.
    """
    id: str = Field(..., description="Unique event ID")
    negotiation_id: str = Field(..., description="Associated negotiation ID")
    event_type: AnalyticsEventType = Field(..., description="Type of event")
    
    # Event timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    turn_number: Optional[int] = Field(None, description="Turn number if applicable")
    round_number: Optional[int] = Field(None, description="Round number if applicable")
    
    # Event data
    agent_id: Optional[str] = Field(None, description="Agent associated with event")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    
    # Performance impact
    performance_impact: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Impact on performance")
    
    # Metadata
    source: str = Field(default="system", description="Event source")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsSummary(BaseModel):
    """
    High-level analytics summary for dashboards.
    """
    id: str = Field(..., description="Unique summary ID")
    
    # Time period
    period_start: datetime = Field(..., description="Summary period start")
    period_end: datetime = Field(..., description="Summary period end")
    
    # Key metrics
    total_negotiations: int = Field(..., description="Total negotiations")
    success_rate: float = Field(ge=0.0, le=1.0, description="Overall success rate")
    average_quality: float = Field(ge=0.0, le=1.0, description="Average agreement quality")
    average_duration: float = Field(..., description="Average negotiation duration")
    
    # Top performers
    top_personalities: List[Dict[str, Any]] = Field(default_factory=list, description="Top performing personalities")
    top_tactics: List[Dict[str, Any]] = Field(default_factory=list, description="Top performing tactics")
    
    # Trends
    success_trend: float = Field(description="Success rate trend")
    quality_trend: float = Field(description="Quality trend")
    efficiency_trend: float = Field(description="Efficiency trend")
    
    # Recommendations
    key_insights: List[str] = Field(default_factory=list, description="Key insights")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
