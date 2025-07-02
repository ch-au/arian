"""
Validation Utilities

This module provides validation functions for agent configurations and negotiation setup.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from ..models.agent import AgentConfig
from ..models.negotiation import NegotiationDimension, DimensionType
from ..models.tactics import TacticLibrary

logger = logging.getLogger(__name__)


def validate_agent_config(agent_config: AgentConfig, tactic_library: Optional[TacticLibrary] = None) -> Dict[str, Any]:
    """
    Validate an agent configuration for completeness and correctness.
    
    Args:
        agent_config: The agent configuration to validate
        tactic_library: Optional tactic library to validate selected tactics against
        
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'completeness_score': 0.0
    }
    
    # Check basic configuration
    if not agent_config.name or len(agent_config.name.strip()) == 0:
        validation_result['errors'].append("Agent name is required")
        validation_result['is_valid'] = False
    
    # Validate personality traits (should be between 0 and 1)
    personality_traits = {
        'openness': agent_config.personality.openness,
        'conscientiousness': agent_config.personality.conscientiousness,
        'extraversion': agent_config.personality.extraversion,
        'agreeableness': agent_config.personality.agreeableness,
        'neuroticism': agent_config.personality.neuroticism
    }
    
    for trait_name, trait_value in personality_traits.items():
        if not 0.0 <= trait_value <= 1.0:
            validation_result['errors'].append(f"Personality trait '{trait_name}' must be between 0.0 and 1.0")
            validation_result['is_valid'] = False
    
    # Validate power level
    if not 0.0 <= agent_config.power_level.level <= 1.0:
        validation_result['errors'].append("Power level must be between 0.0 and 1.0")
        validation_result['is_valid'] = False
    
    # Validate selected tactics
    if tactic_library:
        invalid_tactics = []
        for tactic_id in agent_config.selected_tactics:
            if not tactic_library.get_tactic(tactic_id):
                invalid_tactics.append(tactic_id)
        
        if invalid_tactics:
            validation_result['errors'].append(f"Invalid tactic IDs: {invalid_tactics}")
            validation_result['is_valid'] = False
    
    if not agent_config.selected_tactics:
        validation_result['warnings'].append("No tactics selected - agent may have limited negotiation capabilities")
    
    # Validate ZOPA boundaries
    required_dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
    missing_dimensions = []
    invalid_boundaries = []
    
    for dimension in required_dimensions:
        if dimension not in agent_config.zopa_boundaries:
            missing_dimensions.append(dimension)
        else:
            boundary = agent_config.zopa_boundaries[dimension]
            if 'min_acceptable' not in boundary or 'max_desired' not in boundary:
                invalid_boundaries.append(f"{dimension}: missing min_acceptable or max_desired")
            elif boundary['min_acceptable'] >= boundary['max_desired']:
                invalid_boundaries.append(f"{dimension}: min_acceptable must be less than max_desired")
    
    if missing_dimensions:
        validation_result['errors'].append(f"Missing ZOPA boundaries for dimensions: {missing_dimensions}")
        validation_result['is_valid'] = False
    
    if invalid_boundaries:
        validation_result['errors'].append(f"Invalid ZOPA boundaries: {invalid_boundaries}")
        validation_result['is_valid'] = False
    
    # Calculate completeness score
    completeness_factors = {
        'name': 1.0 if agent_config.name else 0.0,
        'personality': 1.0,  # Always complete if validation passes
        'power_level': 1.0,  # Always complete if validation passes
        'tactics': min(len(agent_config.selected_tactics) / 3, 1.0),  # Ideal: 3+ tactics
        'zopa': len(agent_config.zopa_boundaries) / len(required_dimensions),
        'description': 1.0 if agent_config.description else 0.5
    }
    
    validation_result['completeness_score'] = sum(completeness_factors.values()) / len(completeness_factors)
    
    return validation_result


def validate_negotiation_setup(
    agent1_config: AgentConfig,
    agent2_config: AgentConfig,
    max_rounds: int = 20,
    tactic_library: Optional[TacticLibrary] = None
) -> Dict[str, Any]:
    """
    Validate a complete negotiation setup with two agents.
    
    Args:
        agent1_config: Configuration for the first agent
        agent2_config: Configuration for the second agent
        max_rounds: Maximum number of negotiation rounds
        tactic_library: Optional tactic library for validation
        
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'agent1_validation': {},
        'agent2_validation': {},
        'compatibility_analysis': {}
    }
    
    # Validate individual agents
    validation_result['agent1_validation'] = validate_agent_config(agent1_config, tactic_library)
    validation_result['agent2_validation'] = validate_agent_config(agent2_config, tactic_library)
    
    # Check if individual validations passed
    if not validation_result['agent1_validation']['is_valid']:
        validation_result['errors'].extend([f"Agent 1: {error}" for error in validation_result['agent1_validation']['errors']])
        validation_result['is_valid'] = False
    
    if not validation_result['agent2_validation']['is_valid']:
        validation_result['errors'].extend([f"Agent 2: {error}" for error in validation_result['agent2_validation']['errors']])
        validation_result['is_valid'] = False
    
    # Validate max_rounds
    if not 1 <= max_rounds <= 100:
        validation_result['errors'].append("max_rounds must be between 1 and 100")
        validation_result['is_valid'] = False
    
    # Analyze agent compatibility and ZOPA overlap
    if validation_result['is_valid']:
        compatibility_analysis = analyze_agent_compatibility(agent1_config, agent2_config)
        validation_result['compatibility_analysis'] = compatibility_analysis
        
        # Add warnings based on compatibility analysis
        if compatibility_analysis['zopa_overlap_count'] == 0:
            validation_result['warnings'].append("No ZOPA overlap detected - negotiation may fail")
        elif compatibility_analysis['zopa_overlap_count'] < 3:
            validation_result['warnings'].append("Limited ZOPA overlap - negotiation may be challenging")
        
        if compatibility_analysis['personality_conflict_risk'] > 0.7:
            validation_result['warnings'].append("High personality conflict risk detected")
        
        if compatibility_analysis['power_imbalance'] > 0.6:
            validation_result['warnings'].append("Significant power imbalance detected")
    
    return validation_result


def analyze_agent_compatibility(agent1_config: AgentConfig, agent2_config: AgentConfig) -> Dict[str, Any]:
    """
    Analyze compatibility between two agent configurations.
    
    Args:
        agent1_config: Configuration for the first agent
        agent2_config: Configuration for the second agent
        
    Returns:
        Dictionary with compatibility analysis
    """
    analysis = {
        'zopa_overlap_count': 0,
        'zopa_overlaps': {},
        'personality_conflict_risk': 0.0,
        'power_imbalance': 0.0,
        'tactic_compatibility': 0.0,
        'negotiation_viability': 'unknown'
    }
    
    # Analyze ZOPA overlaps
    common_dimensions = set(agent1_config.zopa_boundaries.keys()) & set(agent2_config.zopa_boundaries.keys())
    
    for dimension in common_dimensions:
        agent1_zopa = agent1_config.zopa_boundaries[dimension]
        agent2_zopa = agent2_config.zopa_boundaries[dimension]
        
        # Check for overlap
        overlap_exists = not (
            agent1_zopa['max_desired'] < agent2_zopa['min_acceptable'] or
            agent2_zopa['max_desired'] < agent1_zopa['min_acceptable']
        )
        
        if overlap_exists:
            analysis['zopa_overlap_count'] += 1
            overlap_min = max(agent1_zopa['min_acceptable'], agent2_zopa['min_acceptable'])
            overlap_max = min(agent1_zopa['max_desired'], agent2_zopa['max_desired'])
            analysis['zopa_overlaps'][dimension] = {
                'overlap_min': overlap_min,
                'overlap_max': overlap_max,
                'overlap_size': overlap_max - overlap_min
            }
    
    # Analyze personality conflict risk
    personality_conflicts = []
    
    # High extraversion vs low extraversion can cause communication issues
    extraversion_diff = abs(agent1_config.personality.extraversion - agent2_config.personality.extraversion)
    if extraversion_diff > 0.6:
        personality_conflicts.append('extraversion_mismatch')
    
    # Low agreeableness on both sides increases conflict risk
    if agent1_config.personality.agreeableness < 0.3 and agent2_config.personality.agreeableness < 0.3:
        personality_conflicts.append('low_agreeableness_both')
    
    # High neuroticism can increase conflict risk
    if agent1_config.personality.neuroticism > 0.7 or agent2_config.personality.neuroticism > 0.7:
        personality_conflicts.append('high_neuroticism')
    
    analysis['personality_conflict_risk'] = min(len(personality_conflicts) * 0.3, 1.0)
    
    # Analyze power imbalance
    power_diff = abs(agent1_config.power_level.level - agent2_config.power_level.level)
    analysis['power_imbalance'] = power_diff
    
    # Analyze tactic compatibility (simplified)
    if agent1_config.selected_tactics and agent2_config.selected_tactics:
        # This is a simplified analysis - in practice, you'd analyze tactic interactions
        analysis['tactic_compatibility'] = 0.5  # Neutral compatibility
    else:
        analysis['tactic_compatibility'] = 0.0  # No tactics selected
    
    # Determine overall negotiation viability
    if analysis['zopa_overlap_count'] >= 3:
        if analysis['personality_conflict_risk'] < 0.5 and analysis['power_imbalance'] < 0.5:
            analysis['negotiation_viability'] = 'high'
        elif analysis['personality_conflict_risk'] < 0.7 and analysis['power_imbalance'] < 0.7:
            analysis['negotiation_viability'] = 'medium'
        else:
            analysis['negotiation_viability'] = 'low'
    elif analysis['zopa_overlap_count'] >= 2:
        analysis['negotiation_viability'] = 'medium'
    elif analysis['zopa_overlap_count'] >= 1:
        analysis['negotiation_viability'] = 'low'
    else:
        analysis['negotiation_viability'] = 'very_low'
    
    return analysis


def validate_negotiation_dimensions(dimensions: List[NegotiationDimension]) -> Dict[str, Any]:
    """
    Validate a list of negotiation dimensions.
    
    Args:
        dimensions: List of negotiation dimensions to validate
        
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'dimension_count': len(dimensions)
    }
    
    if not dimensions:
        validation_result['errors'].append("At least one negotiation dimension is required")
        validation_result['is_valid'] = False
        return validation_result
    
    # Check for required dimensions
    required_types = {DimensionType.VOLUME, DimensionType.PRICE, DimensionType.PAYMENT_TERMS, DimensionType.CONTRACT_DURATION}
    present_types = {dim.name for dim in dimensions}
    missing_types = required_types - present_types
    
    if missing_types:
        validation_result['warnings'].append(f"Missing recommended dimensions: {[t.value for t in missing_types]}")
    
    # Validate each dimension
    for i, dimension in enumerate(dimensions):
        try:
            # Check for ZOPA overlap
            if not dimension.has_overlap():
                validation_result['warnings'].append(f"Dimension '{dimension.name.value}' has no ZOPA overlap")
            
            # Check for reasonable ranges
            if dimension.agent1_min < 0 and dimension.name in [DimensionType.VOLUME, DimensionType.PRICE]:
                validation_result['errors'].append(f"Dimension '{dimension.name.value}': negative values not allowed")
                validation_result['is_valid'] = False
            
        except Exception as e:
            validation_result['errors'].append(f"Dimension {i}: validation error - {e}")
            validation_result['is_valid'] = False
    
    return validation_result


def get_validation_summary(validation_result: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of validation results.
    
    Args:
        validation_result: Validation result dictionary
        
    Returns:
        Human-readable summary string
    """
    if validation_result['is_valid']:
        summary = "✅ Validation passed"
        
        if 'completeness_score' in validation_result:
            score = validation_result['completeness_score']
            summary += f" (Completeness: {score:.1%})"
        
        if validation_result.get('warnings'):
            summary += f"\n⚠️  {len(validation_result['warnings'])} warnings"
    else:
        error_count = len(validation_result['errors'])
        summary = f"❌ Validation failed ({error_count} errors)"
        
        if validation_result.get('warnings'):
            warning_count = len(validation_result['warnings'])
            summary += f", {warning_count} warnings"
    
    return summary
