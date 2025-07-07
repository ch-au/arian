"""
Simple Prompt Manager - Fallback solution without YAML dependency.

This module provides a simplified prompt template manager that uses Python dictionaries
instead of YAML files, ensuring compatibility when PyYAML is not available.
"""

from typing import Dict, List, Optional, Any
from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import NegotiationState


class SimplePromptManager:
    """Simple prompt template manager using Python dictionaries."""
    
    def __init__(self):
        """Initialize with built-in template data."""
        self.template = self._get_template_data()
    
    def _get_template_data(self) -> Dict[str, Any]:
        """Return the template data as a Python dictionary."""
        return {
            'negotiation_agent_prompt': {
                'base_instruction': """You are {agent_name}, a professional negotiator with the following profile:

ROLE: {agent_description}

PERSONALITY PROFILE:
{personality_section}

POWER LEVEL: {power_category} ({power_description})
Power Sources: {power_sources}

NEGOTIATION TACTICS:
{tactics_section}

YOUR ACCEPTABLE RANGES (ZOPA):
{zopa_section}

CURRENT NEGOTIATION STATUS:
{negotiation_status}

INSTRUCTIONS:
{instructions_list}

RESPONSE FORMAT:
{response_format}""",
                
                'personality_templates': {
                    'high_openness': "You are creative and innovative in your approach. You're willing to explore unconventional solutions and think outside the box.",
                    'moderate_openness': "You balance traditional approaches with some creative thinking. You're open to new ideas but prefer proven methods.",
                    'low_openness': "You prefer traditional, proven negotiation approaches. You stick to established methods and value consistency.",
                    
                    'high_conscientiousness': "You are extremely detail-oriented and systematic. You prepare thoroughly and pay close attention to contract terms.",
                    'moderate_conscientiousness': "You are organized and prepared, but can be flexible when needed. You balance detail with practicality.",
                    'low_conscientiousness': "You prefer a flexible, spontaneous approach. You adapt quickly and don't get bogged down in details.",
                    
                    'high_extraversion': "You are confident, assertive, and comfortable taking charge. You speak with authority and make bold moves.",
                    'moderate_extraversion': "You are confident but measured. You speak clearly when needed, but also know when to listen.",
                    'low_extraversion': "You are reserved and thoughtful. You prefer to listen carefully and make well-considered responses.",
                    
                    'high_agreeableness': "You prioritize positive relationships and win-win solutions. You're cooperative and empathetic.",
                    'moderate_agreeableness': "You balance cooperation with your own interests. You collaborate but won't compromise core objectives.",
                    'low_agreeableness': "You are competitive and focused on your objectives. You're willing to use pressure tactics.",
                    
                    'high_neuroticism': "You may show stress in high-pressure situations. You're reactive to setbacks and may express frustration.",
                    'moderate_neuroticism': "You generally remain calm but may show tension during difficult moments. You recover quickly.",
                    'low_neuroticism': "You remain calm under pressure. You don't let emotions affect judgment and maintain steady demeanor."
                },
                
                'personality_thresholds': {
                    'high': 0.7,
                    'moderate_high': 0.6,
                    'moderate': 0.5,
                    'moderate_low': 0.4,
                    'low': 0.3
                },
                
                'tactic_templates': {
                    'collaborative': "Focus on building rapport and finding mutually beneficial solutions. Use phrases like 'How can we both win here?'",
                    'competitive': "Take a firm stance and use leverage strategically. Be willing to walk away if terms aren't favorable.",
                    'anchoring': "Set strong initial reference points to influence the negotiation range. Use market data to support your anchors.",
                    'rapport_building': "Invest time in building personal connections and trust. Find common ground and show genuine interest.",
                    'deadline_pressure': "Create or leverage time constraints to encourage decision-making. Use phrases like 'We need to finalize this by...'",
                    'incremental_concession': "Make small, strategic concessions tied to reciprocal moves from the other party."
                },
                
                'instructions': {
                    'default': [
                        "Stay in character based on your personality profile throughout the negotiation",
                        "Use your selected tactics strategically and appropriately",
                        "Make offers within your ZOPA boundaries, starting closer to your maximum desired terms",
                        "Pay attention to the other party's offers and adjust your strategy accordingly",
                        "Justify your positions with logical reasoning",
                        "Maintain professionalism even when using competitive tactics",
                        "Look for opportunities to create value for both parties",
                        "Be prepared to walk away if terms fall outside your acceptable range"
                    ]
                },
                
                'response_format': """Provide your response in this exact JSON format:
{
  "volume": [integer - number of units],
  "price": [float - price per unit],
  "payment_terms": [integer - days for payment],
  "contract_duration": [integer - months],
  "message": "[string - your negotiation message to the other party]",
  "confidence": [float between 0.0 and 1.0 - how confident you are in this offer],
  "reasoning": "[string - brief explanation of your strategy and reasoning]"
}"""
            }
        }
    
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
            scenario: Optional scenario name (ignored in simple version)
            industry: Optional industry context (ignored in simple version)
            cultural_style: Optional cultural communication style (ignored in simple version)
            
        Returns:
            Complete prompt string with all variables substituted
        """
        template_data = self.template['negotiation_agent_prompt']
        
        # Prepare all variable substitutions
        variables = {
            'agent_name': agent_config.name,
            'agent_description': agent_config.description,
            'personality_section': self._generate_personality_section(agent_config.personality),
            'power_category': agent_config.power_level.get_category(),
            'power_description': agent_config.power_level.description,
            'power_sources': ', '.join(agent_config.power_level.sources),
            'tactics_section': self._generate_tactics_section(agent_config.selected_tactics),
            'zopa_section': self._generate_zopa_section(agent_config.zopa_boundaries),
            'negotiation_status': self._generate_negotiation_status(negotiation_state, agent_config),
            'instructions_list': self._generate_instructions_list(),
            'response_format': template_data['response_format']
        }
        
        # Substitute variables in the base instruction
        prompt = template_data['base_instruction']
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        
        return prompt
    
    def _generate_personality_section(self, personality: PersonalityProfile) -> str:
        """Generate personality instructions based on traits."""
        template_data = self.template['negotiation_agent_prompt']
        personality_templates = template_data['personality_templates']
        thresholds = template_data['personality_thresholds']
        
        traits = []
        
        # Openness
        if personality.openness >= thresholds['high']:
            traits.append(personality_templates['high_openness'])
        elif personality.openness <= thresholds['low']:
            traits.append(personality_templates['low_openness'])
        else:
            traits.append(personality_templates['moderate_openness'])
        
        # Conscientiousness
        if personality.conscientiousness >= thresholds['high']:
            traits.append(personality_templates['high_conscientiousness'])
        elif personality.conscientiousness <= thresholds['low']:
            traits.append(personality_templates['low_conscientiousness'])
        else:
            traits.append(personality_templates['moderate_conscientiousness'])
        
        # Extraversion
        if personality.extraversion >= thresholds['high']:
            traits.append(personality_templates['high_extraversion'])
        elif personality.extraversion <= thresholds['low']:
            traits.append(personality_templates['low_extraversion'])
        else:
            traits.append(personality_templates['moderate_extraversion'])
        
        # Agreeableness
        if personality.agreeableness >= thresholds['high']:
            traits.append(personality_templates['high_agreeableness'])
        elif personality.agreeableness <= thresholds['low']:
            traits.append(personality_templates['low_agreeableness'])
        else:
            traits.append(personality_templates['moderate_agreeableness'])
        
        # Neuroticism
        if personality.neuroticism >= thresholds['high']:
            traits.append(personality_templates['high_neuroticism'])
        elif personality.neuroticism <= thresholds['low']:
            traits.append(personality_templates['low_neuroticism'])
        else:
            traits.append(personality_templates['moderate_neuroticism'])
        
        return "\n".join(filter(None, traits))
    
    def _generate_tactics_section(self, selected_tactics: List[str]) -> str:
        """Generate tactics instructions based on selected tactics."""
        template_data = self.template['negotiation_agent_prompt']
        tactic_templates = template_data['tactic_templates']
        
        if not selected_tactics:
            return "- Use standard negotiation approaches"
        
        tactics_instructions = []
        for tactic_id in selected_tactics:
            if tactic_id in tactic_templates:
                tactics_instructions.append(f"- {tactic_templates[tactic_id]}")
            else:
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
    
    def _generate_instructions_list(self) -> str:
        """Generate the instructions list."""
        template_data = self.template['negotiation_agent_prompt']
        instructions = template_data['instructions']['default']
        
        # Format as numbered list
        formatted_instructions = []
        for i, instruction in enumerate(instructions, 1):
            formatted_instructions.append(f"{i}. {instruction}")
        
        return "\n".join(formatted_instructions)
