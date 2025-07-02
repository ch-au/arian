"""
Agent Factory for creating OpenAI Agents with negotiation configurations.
"""

from typing import Dict, List, Optional
from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import NegotiationState
from models.tactics import TacticLibrary
from .negotiation_agent import NegotiationAgent


class AgentFactory:
    """Factory for creating negotiation agents with OpenAI Agents integration."""
    
    def __init__(self, tactics_library: Optional[TacticLibrary] = None):
        """
        Initialize the agent factory.
        
        Args:
            tactics_library: Library of available negotiation tactics
        """
        self.tactics_library = tactics_library
    
    def create_negotiation_agent(
        self, 
        agent_config: AgentConfig, 
        negotiation_state: NegotiationState
    ) -> NegotiationAgent:
        """
        Create a negotiation agent with OpenAI Agents integration.
        
        Args:
            agent_config: Agent configuration with personality, tactics, etc.
            negotiation_state: Current negotiation state
            
        Returns:
            Configured negotiation agent
        """
        return NegotiationAgent(agent_config, negotiation_state)
    
    def create_buyer_agent(
        self,
        name: str = "Buyer Agent",
        description: str = "Professional procurement manager",
        personality_traits: Optional[Dict[str, float]] = None,
        power_level: float = 0.6,
        power_sources: Optional[List[str]] = None,
        selected_tactics: Optional[List[str]] = None,
        zopa_boundaries: Optional[Dict[str, Dict[str, float]]] = None
    ) -> AgentConfig:
        """
        Create a buyer agent configuration with sensible defaults.
        
        Args:
            name: Agent name
            description: Agent description
            personality_traits: Big 5 personality traits (0.0-1.0)
            power_level: Power level (0.0-1.0)
            power_sources: Sources of negotiation power
            selected_tactics: List of tactic IDs to use
            zopa_boundaries: ZOPA boundaries for each dimension
            
        Returns:
            Configured agent
        """
        # Default personality for a buyer (cost-conscious, detail-oriented)
        if personality_traits is None:
            personality_traits = {
                "openness": 0.6,          # Moderately open to new ideas
                "conscientiousness": 0.8, # Very detail-oriented
                "extraversion": 0.5,      # Balanced communication
                "agreeableness": 0.6,     # Somewhat cooperative
                "neuroticism": 0.4        # Moderately cautious
            }
        
        personality = PersonalityProfile(**personality_traits)
        
        # Default power sources for a buyer
        if power_sources is None:
            power_sources = ["Budget Authority", "Multiple Suppliers", "Market Knowledge"]
        
        power = PowerLevel(
            level=power_level,
            description=f"Buyer with {power_level:.0%} power level",
            sources=power_sources
        )
        
        # Default tactics for a buyer
        if selected_tactics is None:
            selected_tactics = ["collaborative", "anchoring"]
        
        # Default ZOPA boundaries for a buyer (cost-focused)
        if zopa_boundaries is None:
            zopa_boundaries = {
                "volume": {"min_acceptable": 1000, "max_desired": 5000},
                "price": {"min_acceptable": 8.0, "max_desired": 15.0},
                "payment_terms": {"min_acceptable": 30, "max_desired": 90},
                "contract_duration": {"min_acceptable": 6, "max_desired": 24}
            }
        
        return AgentConfig(
            name=name,
            description=description,
            personality=personality,
            power_level=power,
            selected_tactics=selected_tactics,
            zopa_boundaries=zopa_boundaries
        )
    
    def create_seller_agent(
        self,
        name: str = "Seller Agent",
        description: str = "Experienced sales director",
        personality_traits: Optional[Dict[str, float]] = None,
        power_level: float = 0.7,
        power_sources: Optional[List[str]] = None,
        selected_tactics: Optional[List[str]] = None,
        zopa_boundaries: Optional[Dict[str, Dict[str, float]]] = None
    ) -> AgentConfig:
        """
        Create a seller agent configuration with sensible defaults.
        
        Args:
            name: Agent name
            description: Agent description
            personality_traits: Big 5 personality traits (0.0-1.0)
            power_level: Power level (0.0-1.0)
            power_sources: Sources of negotiation power
            selected_tactics: List of tactic IDs to use
            zopa_boundaries: ZOPA boundaries for each dimension
            
        Returns:
            Configured agent
        """
        # Default personality for a seller (confident, relationship-focused)
        if personality_traits is None:
            personality_traits = {
                "openness": 0.7,          # Creative in finding solutions
                "conscientiousness": 0.6, # Organized but flexible
                "extraversion": 0.8,      # Confident and assertive
                "agreeableness": 0.5,     # Balanced cooperation
                "neuroticism": 0.2        # Very calm and confident
            }
        
        personality = PersonalityProfile(**personality_traits)
        
        # Default power sources for a seller
        if power_sources is None:
            power_sources = ["Product Expertise", "Pricing Authority", "Strong Market Position"]
        
        power = PowerLevel(
            level=power_level,
            description=f"Seller with {power_level:.0%} power level",
            sources=power_sources
        )
        
        # Default tactics for a seller
        if selected_tactics is None:
            selected_tactics = ["rapport_building", "competitive"]
        
        # Default ZOPA boundaries for a seller (revenue-focused)
        if zopa_boundaries is None:
            zopa_boundaries = {
                "volume": {"min_acceptable": 2000, "max_desired": 8000},
                "price": {"min_acceptable": 12.0, "max_desired": 20.0},
                "payment_terms": {"min_acceptable": 15, "max_desired": 60},
                "contract_duration": {"min_acceptable": 12, "max_desired": 36}
            }
        
        return AgentConfig(
            name=name,
            description=description,
            personality=personality,
            power_level=power,
            selected_tactics=selected_tactics,
            zopa_boundaries=zopa_boundaries
        )
    
    def create_custom_agent(
        self,
        name: str,
        description: str,
        personality_traits: Dict[str, float],
        power_level: float,
        power_sources: List[str],
        selected_tactics: List[str],
        zopa_boundaries: Dict[str, Dict[str, float]]
    ) -> AgentConfig:
        """
        Create a fully custom agent configuration.
        
        Args:
            name: Agent name
            description: Agent description
            personality_traits: Big 5 personality traits (0.0-1.0)
            power_level: Power level (0.0-1.0)
            power_sources: Sources of negotiation power
            selected_tactics: List of tactic IDs to use
            zopa_boundaries: ZOPA boundaries for each dimension
            
        Returns:
            Configured agent
        """
        personality = PersonalityProfile(**personality_traits)
        
        power = PowerLevel(
            level=power_level,
            description=f"Custom agent with {power_level:.0%} power level",
            sources=power_sources
        )
        
        return AgentConfig(
            name=name,
            description=description,
            personality=personality,
            power_level=power,
            selected_tactics=selected_tactics,
            zopa_boundaries=zopa_boundaries
        )
    
    def get_available_tactics(self) -> List[str]:
        """Get list of available tactic IDs."""
        if self.tactics_library:
            return list(self.tactics_library.tactics.keys())
        else:
            # Return default tactics if no library is provided
            return ["collaborative", "anchoring", "rapport_building", "competitive"]
    
    def validate_agent_config(self, agent_config: AgentConfig) -> Dict[str, bool]:
        """
        Validate an agent configuration.
        
        Args:
            agent_config: Agent configuration to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "personality_valid": True,
            "power_level_valid": True,
            "tactics_valid": True,
            "zopa_valid": True
        }
        
        # Validate personality traits (should be 0.0-1.0)
        personality = agent_config.personality
        for trait_name, trait_value in [
            ("openness", personality.openness),
            ("conscientiousness", personality.conscientiousness),
            ("extraversion", personality.extraversion),
            ("agreeableness", personality.agreeableness),
            ("neuroticism", personality.neuroticism)
        ]:
            if not (0.0 <= trait_value <= 1.0):
                results["personality_valid"] = False
                break
        
        # Validate power level
        if not (0.0 <= agent_config.power_level.level <= 1.0):
            results["power_level_valid"] = False
        
        # Validate tactics (check if they exist in the library)
        if self.tactics_library:
            available_tactics = set(self.tactics_library.tactics.keys())
            selected_tactics = set(agent_config.selected_tactics)
            if not selected_tactics.issubset(available_tactics):
                results["tactics_valid"] = False
        
        # Validate ZOPA boundaries
        for dimension, boundaries in agent_config.zopa_boundaries.items():
            if "min_acceptable" not in boundaries or "max_desired" not in boundaries:
                results["zopa_valid"] = False
                break
            
            min_val = boundaries["min_acceptable"]
            max_val = boundaries["max_desired"]
            
            if min_val >= max_val:
                results["zopa_valid"] = False
                break
        
        return results
