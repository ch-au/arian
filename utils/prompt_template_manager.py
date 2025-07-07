"""
Prompt Template Manager for YAML-based negotiation agent prompts.

This module handles loading, parsing, and generating prompts from YAML templates
with variable substitution and scenario-based modifications.
"""

import yaml
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import NegotiationState


class PromptTemplateManager:
    """Manages YAML-based prompt templates for negotiation agents."""
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the prompt template manager.
        
        Args:
            template_path: Path to the YAML template file. If None, uses default.
        """
        if template_path is None:
            # Default to the template in the prompts directory
            base_dir = Path(__file__).parent.parent
            template_path = base_dir / "prompts" / "negotiation_prompt_template.yaml"
        
        self.template_path = Path(template_path)
        self.template = self._load_template()
        self._validate_template()
    
    def _load_template(self) -> Dict[str, Any]:
        """Load the YAML template file."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
        
        with open(self.template_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _validate_template(self):
        """Validate that the template has required sections."""
        required_sections = [
            'negotiation_agent_prompt',
            'negotiation_agent_prompt.base_instruction',
            'negotiation_agent_prompt.personality_templates',
            'negotiation_agent_prompt.tactic_templates',
            'negotiation_agent_prompt.instructions',
            'negotiation_agent_prompt.response_format'
        ]
        
        for section in required_sections:
            parts = section.split('.')
            current = self.template
            for part in parts:
                if part not in current:
                    raise ValueError(f"Template missing required section: {section}")
                current = current[part]
    
    def generate_prompt(
        self,
        agent_config: AgentConfig,
        negotiation_state: NegotiationState,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        cultural_style: Optional[str] = None
    ) -> str:
        """
        Generate a complete prompt from the template with variable substitution.
        
        Args:
            agent_config: Agent configuration with personality, tactics, etc.
            negotiation_state: Current negotiation state
            scenario: Optional scenario name (e.g., 'aggressive_buyer')
            industry: Optional industry context (e.g., 'technology')
            cultural_style: Optional cultural communication style
            
        Returns:
            Complete prompt string with all variables substituted
        """
        template_data = self.template['negotiation_agent_prompt']
        
        # Prepare all variable substitutions
        variables = {
            'agent_name': agent_config.name,
            'agent_description': agent_config.description,
            'personality_section': self._generate_personality_section(agent_config.personality, scenario),
            'power_category': agent_config.power_level.get_category(),
            'power_description': agent_config.power_level.description,
            'power_sources': ', '.join(agent_config.power_level.sources),
            'tactics_section': self._generate_tactics_section(agent_config.selected_tactics),
            'zopa_section': self._generate_zopa_section(agent_config.zopa_boundaries),
            'negotiation_status': self._generate_negotiation_status(negotiation_state, agent_config),
            'instructions_list': self._generate_instructions_list(scenario, industry, cultural_style),
            'response_format': template_data['response_format']
        }
        
        # Add industry context if specified
        if industry and industry in template_data.get('industry_contexts', {}):
            industry_data = template_data['industry_contexts'][industry]
            variables['agent_description'] += f"\n\nINDUSTRY CONTEXT: {industry_data['context']}"
            
            # Add key factors to instructions
            key_factors = "\n".join([f"- Consider: {factor}" for factor in industry_data['key_factors']])
            variables['instructions_list'] += f"\n\nKey Industry Factors:\n{key_factors}"
        
        # Add cultural style if specified
        if cultural_style and cultural_style in template_data.get('cultural_styles', {}):
            cultural_data = template_data['cultural_styles'][cultural_style]
            modifications = "\n".join(cultural_data['modifications'])
            variables['instructions_list'] += f"\n\nCultural Communication Style ({cultural_data['description']}):\n{modifications}"
        
        # Substitute variables in the base instruction
        prompt = template_data['base_instruction']
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        
        return prompt
    
    def _generate_personality_section(
        self,
        personality: PersonalityProfile,
        scenario: Optional[str] = None
    ) -> str:
        """Generate personality instructions based on traits."""
        template_data = self.template['negotiation_agent_prompt']
        personality_templates = template_data['personality_templates']
        thresholds = template_data.get('personality_thresholds', {
            'high': 0.7,
            'moderate_high': 0.6,
            'moderate': 0.5,
            'moderate_low': 0.4,
            'low': 0.3
        })
        
        # Apply scenario modifiers if specified
        modified_personality = self._apply_scenario_personality_modifiers(personality, scenario)
        
        traits = []
        
        # Openness
        if modified_personality.openness >= thresholds['high']:
            traits.append(personality_templates.get('high_openness', ''))
        elif modified_personality.openness <= thresholds['low']:
            traits.append(personality_templates.get('low_openness', ''))
        else:
            traits.append(personality_templates.get('moderate_openness', ''))
        
        # Conscientiousness
        if modified_personality.conscientiousness >= thresholds['high']:
            traits.append(personality_templates.get('high_conscientiousness', ''))
        elif modified_personality.conscientiousness <= thresholds['low']:
            traits.append(personality_templates.get('low_conscientiousness', ''))
        else:
            traits.append(personality_templates.get('moderate_conscientiousness', ''))
        
        # Extraversion
        if modified_personality.extraversion >= thresholds['high']:
            traits.append(personality_templates.get('high_extraversion', ''))
        elif modified_personality.extraversion <= thresholds['low']:
            traits.append(personality_templates.get('low_extraversion', ''))
        else:
            traits.append(personality_templates.get('moderate_extraversion', ''))
        
        # Agreeableness
        if modified_personality.agreeableness >= thresholds['high']:
            traits.append(personality_templates.get('high_agreeableness', ''))
        elif modified_personality.agreeableness <= thresholds['low']:
            traits.append(personality_templates.get('low_agreeableness', ''))
        else:
            traits.append(personality_templates.get('moderate_agreeableness', ''))
        
        # Neuroticism
        if modified_personality.neuroticism >= thresholds['high']:
            traits.append(personality_templates.get('high_neuroticism', ''))
        elif modified_personality.neuroticism <= thresholds['low']:
            traits.append(personality_templates.get('low_neuroticism', ''))
        else:
            traits.append(personality_templates.get('moderate_neuroticism', ''))
        
        return "\n".join(filter(None, traits))
    
    def _apply_scenario_personality_modifiers(
        self,
        personality: PersonalityProfile,
        scenario: Optional[str]
    ) -> PersonalityProfile:
        """Apply scenario-based personality modifiers."""
        if not scenario:
            return personality
        
        scenarios = self.template['negotiation_agent_prompt'].get('scenarios', {})
        if scenario not in scenarios:
            return personality
        
        modifiers = scenarios[scenario].get('personality_modifiers', {})
        
        # Create a modified personality profile
        modified_traits = {
            'openness': personality.openness,
            'conscientiousness': personality.conscientiousness,
            'extraversion': personality.extraversion,
            'agreeableness': personality.agreeableness,
            'neuroticism': personality.neuroticism
        }
        
        for trait, modifier in modifiers.items():
            if trait in modified_traits:
                # Apply modifier (can be positive or negative)
                if isinstance(modifier, str) and modifier.startswith(('+', '-')):
                    modifier = float(modifier)
                modified_traits[trait] = max(0.0, min(1.0, modified_traits[trait] + modifier))
        
        return PersonalityProfile(**modified_traits)
    
    def _generate_tactics_section(self, selected_tactics: List[str]) -> str:
        """Generate tactics instructions based on selected tactics."""
        template_data = self.template['negotiation_agent_prompt']
        tactic_templates = template_data['tactic_templates']
        
        if not selected_tactics:
            return "- Use standard negotiation approaches"
        
        tactics_instructions = []
        for tactic_id in selected_tactics:
            if tactic_id in tactic_templates:
                tactics_instructions.append(tactic_templates[tactic_id])
            else:
                # Handle unknown tactics gracefully
                tactics_instructions.append(f"- Apply {tactic_id} tactic strategically")
        
        return "\n".join(tactics_instructions)
    
    def _generate_zopa_section(self, zopa_boundaries: Dict[str, Dict[str, float]]) -> str:
        """Generate ZOPA boundaries section."""
        zopa_lines = []
        
        for dimension, boundaries in zopa_boundaries.items():
            min_val = boundaries.get('min_acceptable', 'N/A')
            max_val = boundaries.get('max_desired', 'N/A')
            
            # Format dimension name
            formatted_dimension = dimension.replace('_', ' ').title()
            
            # Add appropriate units based on dimension
            if dimension == 'price':
                zopa_lines.append(f"- {formatted_dimension}: ${min_val} to ${max_val} per unit")
            elif dimension == 'volume':
                zopa_lines.append(f"- {formatted_dimension}: {min_val} to {max_val} units")
            elif dimension == 'payment_terms':
                zopa_lines.append(f"- {formatted_dimension}: {min_val} to {max_val} days")
            elif dimension == 'contract_duration':
                zopa_lines.append(f"- {formatted_dimension}: {min_val} to {max_val} months")
            else:
                zopa_lines.append(f"- {formatted_dimension}: {min_val} to {max_val}")
        
        return "\n".join(zopa_lines)
    
    def _generate_negotiation_status(
        self,
        negotiation_state: NegotiationState,
        agent_config: AgentConfig
    ) -> str:
        """Generate current negotiation status section."""
        status_lines = [
            f"- Round: {negotiation_state.current_round}/{negotiation_state.max_rounds}",
            f"- Total turns taken: {len(negotiation_state.turns)}",
            f"- Total offers made: {len(negotiation_state.offers)}"
        ]
        
        # Determine negotiation stage and add appropriate context
        progress = negotiation_state.current_round / negotiation_state.max_rounds
        if progress <= 0.3:
            stage = 'early_stage'
        elif progress <= 0.7:
            stage = 'middle_stage'
        else:
            stage = 'final_stage'
        
        progress_adaptations = self.template['negotiation_agent_prompt'].get('progress_adaptations', {})
        if stage in progress_adaptations:
            adaptation = progress_adaptations[stage]
            status_lines.append(f"- Stage: {adaptation['focus']}")
        
        # Add information about the other agent's latest offer
        other_agent_id = (negotiation_state.agent2_id 
                         if agent_config.id == negotiation_state.agent1_id 
                         else negotiation_state.agent1_id)
        
        latest_other_offer = negotiation_state.get_latest_offer_by_agent(other_agent_id)
        if latest_other_offer:
            status_lines.append(
                f"- Other party's latest offer: {latest_other_offer.volume} units at "
                f"${latest_other_offer.price}/unit, {latest_other_offer.payment_terms} days payment, "
                f"{latest_other_offer.contract_duration} months"
            )
            status_lines.append(f"- Their message: '{latest_other_offer.message}'")
        else:
            status_lines.append("- No offers from other party yet")
        
        return "\n".join(status_lines)
    
    def _generate_instructions_list(
        self,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        cultural_style: Optional[str] = None
    ) -> str:
        """Generate the instructions list, including scenario-specific additions."""
        template_data = self.template['negotiation_agent_prompt']
        
        # Start with default instructions
        instructions = list(template_data['instructions'].get('default', []))
        
        # Add scenario-specific instructions
        if scenario and scenario in template_data.get('scenarios', {}):
            scenario_data = template_data['scenarios'][scenario]
            additional = scenario_data.get('additional_instructions', [])
            if additional:
                instructions.append(f"\n{scenario_data['name']}:")
                instructions.extend(additional)
        
        # Format as numbered list
        formatted_instructions = []
        for i, instruction in enumerate(instructions, 1):
            if instruction.startswith('\n'):
                # This is a section header
                formatted_instructions.append(instruction)
            else:
                formatted_instructions.append(f"{i}. {instruction}")
        
        return "\n".join(formatted_instructions)
    
    def get_available_scenarios(self) -> List[str]:
        """Get list of available scenario names."""
        scenarios = self.template['negotiation_agent_prompt'].get('scenarios', {})
        return list(scenarios.keys())
    
    def get_available_industries(self) -> List[str]:
        """Get list of available industry contexts."""
        industries = self.template['negotiation_agent_prompt'].get('industry_contexts', {})
        return list(industries.keys())
    
    def get_available_cultural_styles(self) -> List[str]:
        """Get list of available cultural communication styles."""
        styles = self.template['negotiation_agent_prompt'].get('cultural_styles', {})
        return list(styles.keys())
    
    def reload_template(self):
        """Reload the template from disk (useful for development)."""
        self.template = self._load_template()
        self._validate_template()
