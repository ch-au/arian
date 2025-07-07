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
try:
    from utils.prompt_template_manager import PromptTemplateManager
except ImportError:
    # Fallback to simple prompt manager if YAML is not available
    from utils.simple_prompt_manager import SimplePromptManager as PromptTemplateManager


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
    
    def __init__(
        self, 
        agent_config: AgentConfig, 
        negotiation_state: NegotiationState,
        template_path: Optional[str] = None,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        cultural_style: Optional[str] = None
    ):
        """
        Initialize the negotiation agent.
        
        Args:
            agent_config: Our custom agent configuration
            negotiation_state: Current negotiation state
            template_path: Optional path to custom YAML template
            scenario: Optional scenario name (e.g., 'aggressive_buyer')
            industry: Optional industry context (e.g., 'technology')
            cultural_style: Optional cultural communication style
        """
        self.agent_config = agent_config
        self.negotiation_state = negotiation_state
        self.scenario = scenario
        self.industry = industry
        self.cultural_style = cultural_style
        
        # Initialize the prompt template manager
        self.prompt_manager = PromptTemplateManager(template_path)
        
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
        """Generate detailed instructions using the YAML template."""
        return self.prompt_manager.generate_prompt(
            agent_config=self.agent_config,
            negotiation_state=self.negotiation_state,
            scenario=self.scenario,
            industry=self.industry,
            cultural_style=self.cultural_style
        )
    
    
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
