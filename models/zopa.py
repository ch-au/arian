"""
ZOPA (Zone of Possible Agreement) Analysis Models

This module defines the data models for ZOPA analysis including:
- ZOPA boundary definitions
- Overlap analysis between agents
- ZOPA utilization metrics
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, validator
from enum import Enum
import statistics


class ZOPAStatus(str, Enum):
    """Status of ZOPA analysis between two agents."""
    NO_OVERLAP = "no_overlap"
    PARTIAL_OVERLAP = "partial_overlap"
    FULL_OVERLAP = "full_overlap"
    IDENTICAL_RANGES = "identical_ranges"


class ZOPABoundary(BaseModel):
    """
    Represents ZOPA boundaries for a single agent on a single dimension.
    """
    
    agent_id: str = Field(..., description="ID of the agent")
    dimension: str = Field(..., description="Name of the negotiation dimension")
    
    min_acceptable: float = Field(..., description="Minimum acceptable value (walk-away point)")
    max_desired: float = Field(..., description="Maximum desired value (ideal outcome)")
    
    # Optional preference curve data
    preferred_value: Optional[float] = Field(default=None, description="Most preferred value within range")
    preference_weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Importance of this dimension (0-1)")
    
    # Flexibility indicators
    flexibility_score: float = Field(default=0.5, ge=0.0, le=1.0, description="How flexible the agent is on this dimension")
    concession_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Rate at which agent makes concessions")
    
    @validator('max_desired')
    def validate_max_greater_than_min(cls, v, values):
        """Ensure max_desired is greater than min_acceptable."""
        min_val = values.get('min_acceptable')
        if min_val is not None and v <= min_val:
            raise ValueError("max_desired must be greater than min_acceptable")
        return v
    
    @validator('preferred_value')
    def validate_preferred_in_range(cls, v, values):
        """Ensure preferred_value is within the acceptable range."""
        if v is None:
            return v
        
        min_val = values.get('min_acceptable')
        max_val = values.get('max_desired')
        
        if min_val is not None and max_val is not None:
            if not (min_val <= v <= max_val):
                raise ValueError("preferred_value must be between min_acceptable and max_desired")
        
        return v
    
    def get_range_size(self) -> float:
        """Calculate the size of the acceptable range."""
        return self.max_desired - self.min_acceptable
    
    def get_midpoint(self) -> float:
        """Get the midpoint of the acceptable range."""
        return (self.min_acceptable + self.max_desired) / 2
    
    def get_effective_preferred(self) -> float:
        """Get the preferred value, defaulting to midpoint if not specified."""
        return self.preferred_value if self.preferred_value is not None else self.get_midpoint()
    
    def is_value_acceptable(self, value: float) -> bool:
        """Check if a value is within the acceptable range."""
        return self.min_acceptable <= value <= self.max_desired
    
    def calculate_satisfaction(self, value: float) -> float:
        """
        Calculate satisfaction score (0-1) for a given value.
        
        Returns 0 if outside acceptable range, 1 if at preferred value,
        and interpolated values in between.
        """
        if not self.is_value_acceptable(value):
            return 0.0
        
        preferred = self.get_effective_preferred()
        
        if value == preferred:
            return 1.0
        
        # Calculate distance from preferred value as a fraction of total range
        range_size = self.get_range_size()
        if range_size == 0:
            return 1.0  # Single point range
        
        distance_from_preferred = abs(value - preferred)
        max_distance = max(
            abs(self.min_acceptable - preferred),
            abs(self.max_desired - preferred)
        )
        
        if max_distance == 0:
            return 1.0
        
        # Linear satisfaction decay from preferred value
        satisfaction = 1.0 - (distance_from_preferred / max_distance)
        return max(0.0, satisfaction)


class ZOPAOverlap(BaseModel):
    """
    Represents the overlap between two agents' ZOPA boundaries on a dimension.
    """
    
    dimension: str = Field(..., description="Name of the negotiation dimension")
    agent1_boundary: ZOPABoundary = Field(..., description="Agent 1's ZOPA boundary")
    agent2_boundary: ZOPABoundary = Field(..., description="Agent 2's ZOPA boundary")
    
    # Calculated overlap data
    has_overlap: bool = Field(..., description="Whether any overlap exists")
    overlap_min: Optional[float] = Field(default=None, description="Minimum value of overlap range")
    overlap_max: Optional[float] = Field(default=None, description="Maximum value of overlap range")
    overlap_size: float = Field(default=0.0, description="Size of the overlap range")
    
    # Analysis metrics
    overlap_percentage: float = Field(default=0.0, ge=0.0, le=1.0, description="Overlap as % of total range")
    mutual_satisfaction_potential: float = Field(default=0.0, ge=0.0, le=1.0, description="Potential for mutual satisfaction")
    
    def __init__(self, **data):
        """Initialize and calculate overlap metrics."""
        # Auto-calculate required fields if not provided
        if 'has_overlap' not in data:
            data['has_overlap'] = self._calculate_has_overlap(data.get('agent1_boundary'), data.get('agent2_boundary'))
        if 'overlap_min' not in data:
            data['overlap_min'] = 0.0
        if 'overlap_max' not in data:
            data['overlap_max'] = 0.0
        if 'overlap_size' not in data:
            data['overlap_size'] = 0.0
        if 'mutual_satisfaction_score' not in data:
            data['mutual_satisfaction_score'] = 0.0
        if 'optimal_value' not in data:
            data['optimal_value'] = None
        
        super().__init__(**data)
        self._calculate_overlap()
    
    def _calculate_has_overlap(self, boundary1, boundary2) -> bool:
        """Calculate if there's overlap between two boundaries."""
        if not boundary1 or not boundary2:
            return False
        
        # Check if ranges overlap
        return not (boundary1.max_desired < boundary2.min_acceptable or 
                   boundary2.max_desired < boundary1.min_acceptable)
    
    def _calculate_overlap(self) -> None:
        """Calculate overlap metrics between the two boundaries."""
        agent1 = self.agent1_boundary
        agent2 = self.agent2_boundary
        
        # Check for overlap
        self.has_overlap = not (agent1.max_desired < agent2.min_acceptable or 
                               agent2.max_desired < agent1.min_acceptable)
        
        if self.has_overlap:
            self.overlap_min = max(agent1.min_acceptable, agent2.min_acceptable)
            self.overlap_max = min(agent1.max_desired, agent2.max_desired)
            self.overlap_size = self.overlap_max - self.overlap_min
            
            # Calculate overlap percentage relative to combined range
            total_range_min = min(agent1.min_acceptable, agent2.min_acceptable)
            total_range_max = max(agent1.max_desired, agent2.max_desired)
            total_range_size = total_range_max - total_range_min
            
            if total_range_size > 0:
                self.overlap_percentage = self.overlap_size / total_range_size
            else:
                self.overlap_percentage = 1.0  # Identical single points
            
            # Calculate mutual satisfaction potential
            self._calculate_mutual_satisfaction_potential()
        else:
            self.overlap_min = None
            self.overlap_max = None
            self.overlap_size = 0.0
            self.overlap_percentage = 0.0
            self.mutual_satisfaction_potential = 0.0
    
    def _calculate_mutual_satisfaction_potential(self) -> None:
        """Calculate the potential for mutual satisfaction in the overlap zone."""
        if not self.has_overlap:
            self.mutual_satisfaction_potential = 0.0
            return
        
        # Sample points in the overlap range and calculate average mutual satisfaction
        sample_points = []
        num_samples = 10
        
        for i in range(num_samples + 1):
            if self.overlap_size == 0:
                value = self.overlap_min
            else:
                value = self.overlap_min + (i / num_samples) * self.overlap_size
            
            sat1 = self.agent1_boundary.calculate_satisfaction(value)
            sat2 = self.agent2_boundary.calculate_satisfaction(value)
            mutual_sat = (sat1 + sat2) / 2  # Average satisfaction
            sample_points.append(mutual_sat)
        
        self.mutual_satisfaction_potential = max(sample_points) if sample_points else 0.0
    
    def get_optimal_value(self) -> Optional[float]:
        """
        Find the value in the overlap range that maximizes mutual satisfaction.
        
        Returns None if no overlap exists.
        """
        if not self.has_overlap:
            return None
        
        if self.overlap_size == 0:
            return self.overlap_min
        
        # Search for optimal value using grid search
        best_value = self.overlap_min
        best_satisfaction = 0.0
        
        num_samples = 100
        for i in range(num_samples + 1):
            value = self.overlap_min + (i / num_samples) * self.overlap_size
            
            sat1 = self.agent1_boundary.calculate_satisfaction(value)
            sat2 = self.agent2_boundary.calculate_satisfaction(value)
            mutual_sat = (sat1 + sat2) / 2
            
            if mutual_sat > best_satisfaction:
                best_satisfaction = mutual_sat
                best_value = value
        
        return best_value
    
    def get_status(self) -> ZOPAStatus:
        """Get the status of the ZOPA overlap."""
        if not self.has_overlap:
            return ZOPAStatus.NO_OVERLAP
        
        agent1 = self.agent1_boundary
        agent2 = self.agent2_boundary
        
        # Check for identical ranges
        if (agent1.min_acceptable == agent2.min_acceptable and 
            agent1.max_desired == agent2.max_desired):
            return ZOPAStatus.IDENTICAL_RANGES
        
        # Check overlap percentage
        if self.overlap_percentage >= 0.8:
            return ZOPAStatus.FULL_OVERLAP
        else:
            return ZOPAStatus.PARTIAL_OVERLAP
    
    def get_negotiation_difficulty(self) -> str:
        """Assess the difficulty of reaching agreement on this dimension."""
        if not self.has_overlap:
            return "Impossible - No ZOPA"
        
        if self.mutual_satisfaction_potential >= 0.8:
            return "Easy - High mutual satisfaction potential"
        elif self.mutual_satisfaction_potential >= 0.6:
            return "Moderate - Good potential for agreement"
        elif self.mutual_satisfaction_potential >= 0.4:
            return "Challenging - Limited mutual satisfaction"
        else:
            return "Very Difficult - Low mutual satisfaction potential"


class ZOPAAnalysis(BaseModel):
    """
    Complete ZOPA analysis for a multi-dimensional negotiation.
    
    Analyzes overlaps across all dimensions and provides overall assessment.
    """
    
    negotiation_id: str = Field(..., description="ID of the negotiation being analyzed")
    agent1_id: str = Field(..., description="ID of the first agent")
    agent2_id: str = Field(..., description="ID of the second agent")
    
    dimension_overlaps: List[ZOPAOverlap] = Field(..., description="Overlap analysis for each dimension")
    
    # Overall metrics
    total_dimensions: int = Field(..., ge=1, description="Total number of dimensions")
    dimensions_with_overlap: int = Field(default=0, ge=0, description="Number of dimensions with overlap")
    overall_overlap_percentage: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall overlap percentage")
    
    # Negotiation viability
    negotiation_viable: bool = Field(default=False, description="Whether negotiation is viable")
    viability_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall viability score")
    
    # Recommendations
    recommended_strategy: str = Field(default="", description="Recommended negotiation strategy")
    critical_dimensions: List[str] = Field(default_factory=list, description="Dimensions requiring most attention")
    
    def __init__(self, **data):
        """Initialize and calculate overall analysis."""
        super().__init__(**data)
        self._calculate_overall_metrics()
        self._generate_recommendations()
    
    def _calculate_overall_metrics(self) -> None:
        """Calculate overall ZOPA metrics across all dimensions."""
        self.total_dimensions = len(self.dimension_overlaps)
        self.dimensions_with_overlap = sum(1 for overlap in self.dimension_overlaps if overlap.has_overlap)
        
        if self.total_dimensions > 0:
            # Calculate overall overlap percentage as average of dimension overlaps
            overlap_percentages = [overlap.overlap_percentage for overlap in self.dimension_overlaps]
            self.overall_overlap_percentage = statistics.mean(overlap_percentages)
            
            # Negotiation is viable if at least 75% of dimensions have overlap
            overlap_ratio = self.dimensions_with_overlap / self.total_dimensions
            self.negotiation_viable = overlap_ratio >= 0.75
            
            # Calculate viability score
            satisfaction_scores = [overlap.mutual_satisfaction_potential for overlap in self.dimension_overlaps]
            avg_satisfaction = statistics.mean(satisfaction_scores)
            self.viability_score = overlap_ratio * 0.6 + avg_satisfaction * 0.4
    
    def _generate_recommendations(self) -> None:
        """Generate negotiation strategy recommendations."""
        if not self.negotiation_viable:
            self.recommended_strategy = "Focus on expanding ZOPA through creative problem-solving and value creation"
            self.critical_dimensions = [
                overlap.dimension for overlap in self.dimension_overlaps 
                if not overlap.has_overlap
            ]
        else:
            # Identify strategy based on overlap patterns
            high_satisfaction_dims = [
                overlap.dimension for overlap in self.dimension_overlaps 
                if overlap.mutual_satisfaction_potential >= 0.7
            ]
            
            low_satisfaction_dims = [
                overlap.dimension for overlap in self.dimension_overlaps 
                if overlap.has_overlap and overlap.mutual_satisfaction_potential < 0.4
            ]
            
            if len(high_satisfaction_dims) >= len(low_satisfaction_dims):
                self.recommended_strategy = "Build momentum with easy wins on high-satisfaction dimensions first"
            else:
                self.recommended_strategy = "Address challenging dimensions early with creative trade-offs"
            
            self.critical_dimensions = low_satisfaction_dims
    
    def get_dimension_analysis(self, dimension: str) -> Optional[ZOPAOverlap]:
        """Get overlap analysis for a specific dimension."""
        for overlap in self.dimension_overlaps:
            if overlap.dimension == dimension:
                return overlap
        return None
    
    def get_optimal_package(self) -> Optional[Dict[str, float]]:
        """
        Calculate an optimal package deal across all dimensions.
        
        Returns None if no viable package exists.
        """
        if not self.negotiation_viable:
            return None
        
        optimal_package = {}
        
        for overlap in self.dimension_overlaps:
            if overlap.has_overlap:
                optimal_value = overlap.get_optimal_value()
                if optimal_value is not None:
                    optimal_package[overlap.dimension] = optimal_value
            else:
                # For dimensions without overlap, suggest midpoint between ranges
                agent1_mid = overlap.agent1_boundary.get_midpoint()
                agent2_mid = overlap.agent2_boundary.get_midpoint()
                optimal_package[overlap.dimension] = (agent1_mid + agent2_mid) / 2
        
        return optimal_package if optimal_package else None
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive summary report."""
        return {
            "negotiation_id": self.negotiation_id,
            "viability": {
                "is_viable": self.negotiation_viable,
                "viability_score": round(self.viability_score, 3),
                "dimensions_with_overlap": f"{self.dimensions_with_overlap}/{self.total_dimensions}",
                "overall_overlap_percentage": round(self.overall_overlap_percentage * 100, 1)
            },
            "dimension_analysis": [
                {
                    "dimension": overlap.dimension,
                    "has_overlap": overlap.has_overlap,
                    "overlap_size": round(overlap.overlap_size, 2) if overlap.has_overlap else 0,
                    "mutual_satisfaction_potential": round(overlap.mutual_satisfaction_potential, 3),
                    "status": overlap.get_status().value,
                    "difficulty": overlap.get_negotiation_difficulty()
                }
                for overlap in self.dimension_overlaps
            ],
            "recommendations": {
                "strategy": self.recommended_strategy,
                "critical_dimensions": self.critical_dimensions,
                "optimal_package": self.get_optimal_package()
            }
        }
    
    @classmethod
    def from_agent_configs(
        cls,
        negotiation_id: str,
        agent1_config: "AgentConfig",
        agent2_config: "AgentConfig"
    ) -> "ZOPAAnalysis":
        """
        Create ZOPA analysis from two agent configurations.
        
        Args:
            negotiation_id: ID of the negotiation
            agent1_config: Configuration for agent 1
            agent2_config: Configuration for agent 2
            
        Returns:
            Complete ZOPA analysis
        """
        dimension_overlaps = []
        
        # Get all dimensions from both agents
        all_dimensions = set(agent1_config.zopa_boundaries.keys()) | set(agent2_config.zopa_boundaries.keys())
        
        for dimension in all_dimensions:
            # Get boundaries for both agents
            agent1_zopa = agent1_config.get_zopa_for_dimension(dimension)
            agent2_zopa = agent2_config.get_zopa_for_dimension(dimension)
            
            if agent1_zopa and agent2_zopa:
                # Create ZOPA boundaries
                boundary1 = ZOPABoundary(
                    agent_id=agent1_config.id,
                    dimension=dimension,
                    min_acceptable=agent1_zopa['min_acceptable'],
                    max_desired=agent1_zopa['max_desired']
                )
                
                boundary2 = ZOPABoundary(
                    agent_id=agent2_config.id,
                    dimension=dimension,
                    min_acceptable=agent2_zopa['min_acceptable'],
                    max_desired=agent2_zopa['max_desired']
                )
                
                # Create overlap analysis
                overlap = ZOPAOverlap(
                    dimension=dimension,
                    agent1_boundary=boundary1,
                    agent2_boundary=boundary2
                )
                
                dimension_overlaps.append(overlap)
        
        return cls(
            negotiation_id=negotiation_id,
            agent1_id=agent1_config.id,
            agent2_id=agent2_config.id,
            dimension_overlaps=dimension_overlaps
        )
