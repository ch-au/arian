"""
Negotiation Agent using OpenAI Agents Framework

This module creates negotiation agents that use the OpenAI Agents framework
with our personality, tactics, and ZOPA configurations.
"""

from typing import Dict, List, Optional, Any
try:
    from agents import Agent, function_tool, Runner
except ImportError:
    # Fallback for when openai-agents is not available
    Agent = None
    function_tool = None
    Runner = None
from pydantic import BaseModel

from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import NegotiationOffer, NegotiationState, NegotiationDimension
from models.tactics import NegotiationTactic


class NegotiationOfferOutput(BaseModel):
    """Structured output for negotiation offers."""
    volume: int
    price: float
    payment_terms: int
    contract_duration: int
    message: str
    confidence: float
    reasoning: str


class NegotiationAgent:
    """
    A negotiation agent that uses OpenAI Agents framework with our custom configuration.
    """
    
    def __init__(self, agent_config: AgentConfig, negotiation_state: NegotiationState):
        """
        Initialize the negotiation agent.
        
        Args:
            agent_config: Our custom agent configuration
            negotiation_state: Current negotiation state
        """
        self.agent_config = agent_config
        self.negotiation_state = negotiation_state
        self.openai_agent = self._create_openai_agent()
    
    def _create_openai_agent(self) -> Agent:
        """Create an OpenAI Agent with our custom configuration."""
        
        # Generate personality-based instructions
        instructions = self._generate_instructions()
        
        # Create the OpenAI Agent
        agent = Agent(
            name=self.agent_config.name,
            instructions=instructions,
            output_type=NegotiationOfferOutput,
            tools=[self._create_negotiation_tools()]
        )
        
        return agent
    
    def _generate_instructions(self) -> str:
        """Generate detailed instructions based on agent configuration."""
        
        # Base instructions
        instructions = f"""You are {self.agent_config.name}, a professional negotiator.

ROLE: {self.agent_config.description}

PERSONALITY PROFILE:
{self._format_personality_instructions()}

POWER LEVEL: {self.agent_config.power_level.get_category()} ({self.agent_config.power_level.description})
Power Sources: {', '.join(self.agent_config.power_level.sources)}

NEGOTIATION TACTICS:
{self._format_tactics_instructions()}

ZOPA BOUNDARIES (Your acceptable ranges):
{self._format_zopa_instructions()}

CURRENT NEGOTIATION STATUS:
{self._format_negotiation_status()}

INSTRUCTIONS:
1. Always make offers within your ZOPA boundaries
2. Apply your selected negotiation tactics in your communication style
3. Consider your personality traits when crafting responses
4. Use your power level to determine how assertive or flexible to be
5. Aim for win-win solutions while protecting your interests
6. Provide clear reasoning for your offers
7. Be professional but let your personality show through

RESPONSE FORMAT:
- volume: Number of units (integer)
- price: Price per unit (float)
- payment_terms: Payment period in days (integer)
- contract_duration: Contract length in months (integer)
- message: Your negotiation message (string)
- confidence: Your confidence in this offer 0.0-1.0 (float)
- reasoning: Why you made this offer (string)
"""
        
        return instructions
    
    def _format_personality_instructions(self) -> str:
        """Format personality traits into instructions."""
        personality = self.agent_config.personality
        
        traits = []
        if personality.openness >= 0.7:
            traits.append("- Be creative and open to innovative solutions")
        elif personality.openness <= 0.3:
            traits.append("- Prefer traditional, proven approaches")
        
        if personality.conscientiousness >= 0.7:
            traits.append("- Be detail-oriented and systematic in your approach")
        elif personality.conscientiousness <= 0.3:
            traits.append("- Be flexible and adaptable to changing circumstances")
        
        if personality.extraversion >= 0.7:
            traits.append("- Be confident, assertive, and direct in communication")
        elif personality.extraversion <= 0.3:
            traits.append("- Be thoughtful, reserved, and measured in responses")
        
        if personality.agreeableness >= 0.7:
            traits.append("- Emphasize collaboration and mutual benefits")
        elif personality.agreeableness <= 0.3:
            traits.append("- Be competitive and focus on your own interests")
        
        if personality.neuroticism >= 0.7:
            traits.append("- Be cautious and risk-averse in your offers")
        elif personality.neuroticism <= 0.3:
            traits.append("- Be calm and confident under pressure")
        
        return "\n".join(traits) if traits else "- Maintain a balanced approach"
    
    def _format_tactics_instructions(self) -> str:
        """Format selected tactics into instructions."""
        if not self.agent_config.selected_tactics:
            return "- Use standard negotiation approaches"
        
        # In a real implementation, you would load the actual tactics
        # For now, we'll use the tactic names as guidance
        tactics_guidance = []
        for tactic_id in self.agent_config.selected_tactics:
            if "collaborative" in tactic_id.lower():
                tactics_guidance.append("- Use collaborative language and seek mutual benefits")
            elif "anchoring" in tactic_id.lower():
                tactics_guidance.append("- Make strong opening offers to anchor expectations")
            elif "rapport" in tactic_id.lower():
                tactics_guidance.append("- Build personal connection and establish trust")
            elif "competitive" in tactic_id.lower():
                tactics_guidance.append("- Highlight your strong position and alternatives")
        
        return "\n".join(tactics_guidance) if tactics_guidance else "- Apply your selected tactics strategically"
    
    def _format_zopa_instructions(self) -> str:
        """Format ZOPA boundaries into instructions."""
        zopa_text = []
        for dimension, boundaries in self.agent_config.zopa_boundaries.items():
            min_val = boundaries['min_acceptable']
            max_val = boundaries['max_desired']
            zopa_text.append(f"- {dimension.replace('_', ' ').title()}: {min_val} to {max_val}")
        
        return "\n".join(zopa_text)
    
    def _format_negotiation_status(self) -> str:
        """Format current negotiation status."""
        status_text = [
            f"- Round: {self.negotiation_state.current_round}/{self.negotiation_state.max_rounds}",
            f"- Total turns taken: {len(self.negotiation_state.turns)}",
            f"- Total offers made: {len(self.negotiation_state.offers)}"
        ]
        
        # Add information about the other agent's latest offer
        other_agent_id = (self.negotiation_state.agent2_id 
                         if self.agent_config.id == self.negotiation_state.agent1_id 
                         else self.negotiation_state.agent1_id)
        
        latest_other_offer = self.negotiation_state.get_latest_offer_by_agent(other_agent_id)
        if latest_other_offer:
            status_text.append(f"- Other party's latest offer: {latest_other_offer.volume} units at ${latest_other_offer.price}/unit, {latest_other_offer.payment_terms} days payment, {latest_other_offer.contract_duration} months")
            status_text.append(f"- Their message: '{latest_other_offer.message}'")
        else:
            status_text.append("- No offers from other party yet")
        
        return "\n".join(status_text)
    
    def _create_negotiation_tools(self):
        """Create tools for the negotiation agent."""
        
        @function_tool
        def analyze_zopa_overlap(dimension: str) -> str:
            """Analyze ZOPA overlap for a specific dimension."""
            for dim in self.negotiation_state.dimensions:
                if dim.name.value == dimension:
                    if dim.has_overlap():
                        overlap = dim.get_overlap_range()
                        return f"ZOPA overlap for {dimension}: {overlap[0]} to {overlap[1]} {dim.unit}"
                    else:
                        return f"No ZOPA overlap for {dimension} - negotiation will be challenging"
            return f"Dimension {dimension} not found"
        
        @function_tool
        def get_negotiation_history() -> str:
            """Get a summary of the negotiation history."""
            if not self.negotiation_state.offers:
                return "No offers have been made yet."
            
            history = []
            for i, offer in enumerate(self.negotiation_state.offers, 1):
                agent_name = "You" if offer.agent_id == self.agent_config.id else "Other party"
                history.append(f"Offer {i} ({agent_name}): {offer.volume} units, ${offer.price}/unit, {offer.payment_terms} days, {offer.contract_duration} months")
            
            return "\n".join(history)
        
        @function_tool
        def calculate_offer_value(volume: int, price: float) -> str:
            """Calculate the total value of an offer."""
            total_value = volume * price
            return f"Total offer value: ${total_value:,.2f}"
        
        return analyze_zopa_overlap
    
    async def make_offer(self, context: str = "") -> NegotiationOfferOutput:
        """
        Make a negotiation offer using the OpenAI Agent.
        
        Args:
            context: Additional context for the offer
            
        Returns:
            Structured negotiation offer
        """
        from agents import Runner
        
        # Prepare the input message
        input_message = f"Make your next negotiation offer. {context}".strip()
        
        # Run the agent
        result = await Runner.run(self.openai_agent, input_message)
        
        return result.final_output
    
    def update_negotiation_state(self, negotiation_state: NegotiationState):
        """Update the negotiation state and refresh instructions."""
        self.negotiation_state = negotiation_state
        # Recreate the agent with updated instructions
        self.openai_agent = self._create_openai_agent()
