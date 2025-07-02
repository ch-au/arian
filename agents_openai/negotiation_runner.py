"""
Negotiation Runner using OpenAI Agents Framework

This module orchestrates complete negotiations between two OpenAI agents.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from models.agent import AgentConfig
from models.negotiation import (
    NegotiationState, 
    NegotiationDimension, 
    NegotiationOffer,
    NegotiationTurn,
    TurnType,
    NegotiationStatus
)
from .negotiation_agent import NegotiationAgent, NegotiationOfferOutput
from .agent_factory import AgentFactory

logger = logging.getLogger(__name__)


class NegotiationRunner:
    """
    Orchestrates negotiations between two OpenAI agents.
    """
    
    def __init__(self, agent_factory: Optional[AgentFactory] = None):
        """
        Initialize the negotiation runner.
        
        Args:
            agent_factory: Factory for creating agents
        """
        self.agent_factory = agent_factory or AgentFactory()
        self.current_negotiation: Optional[NegotiationState] = None
        self.agent1: Optional[NegotiationAgent] = None
        self.agent2: Optional[NegotiationAgent] = None
    
    async def run_negotiation(
        self,
        agent1_config: AgentConfig,
        agent2_config: AgentConfig,
        dimensions: List[NegotiationDimension],
        max_rounds: int = 10,
        verbose: bool = True
    ) -> NegotiationState:
        """
        Run a complete negotiation between two agents.
        
        Args:
            agent1_config: Configuration for the first agent
            agent2_config: Configuration for the second agent
            dimensions: Negotiation dimensions
            max_rounds: Maximum number of rounds
            verbose: Whether to print progress
            
        Returns:
            Final negotiation state
        """
        # Create negotiation state
        self.current_negotiation = NegotiationState(
            agent1_id=agent1_config.id,
            agent2_id=agent2_config.id,
            max_rounds=max_rounds,
            dimensions=dimensions
        )
        
        # Create agents
        self.agent1 = self.agent_factory.create_negotiation_agent(
            agent1_config, self.current_negotiation
        )
        self.agent2 = self.agent_factory.create_negotiation_agent(
            agent2_config, self.current_negotiation
        )
        
        if verbose:
            print(f"🚀 Starting negotiation between {agent1_config.name} and {agent2_config.name}")
            print(f"📊 Max rounds: {max_rounds}")
            print(f"📏 Dimensions: {[dim.name.value for dim in dimensions]}")
            self._print_zopa_analysis(dimensions)
        
        # Start the negotiation
        self.current_negotiation.start_negotiation()
        
        # Main negotiation loop
        while True:
            # Check termination conditions
            should_terminate, reason = self.current_negotiation.should_terminate()
            if should_terminate:
                if verbose:
                    print(f"\n🏁 Negotiation terminating: {reason}")
                break
            
            # Determine current agent
            current_agent = (self.agent1 if self.current_negotiation.current_turn_agent == agent1_config.id 
                           else self.agent2)
            current_config = (agent1_config if current_agent == self.agent1 else agent2_config)
            
            if verbose:
                print(f"\n--- Round {self.current_negotiation.current_round}, Turn {len(self.current_negotiation.turns) + 1} ---")
                print(f"🎯 {current_config.name}'s turn")
            
            # Execute turn
            try:
                await self._execute_turn(current_agent, current_config, verbose)
            except Exception as e:
                logger.error(f"Error during turn execution: {e}")
                if verbose:
                    print(f"❌ Error during {current_config.name}'s turn: {e}")
                break
            
            # Update both agents with the new state
            self.agent1.update_negotiation_state(self.current_negotiation)
            self.agent2.update_negotiation_state(self.current_negotiation)
        
        # Finalize negotiation
        result = self.current_negotiation.finalize_negotiation(reason)
        
        if verbose:
            self._print_final_results(result)
        
        return self.current_negotiation
    
    async def _execute_turn(
        self, 
        agent: NegotiationAgent, 
        agent_config: AgentConfig,
        verbose: bool = True
    ) -> None:
        """Execute a single turn in the negotiation."""
        start_time = datetime.now()
        
        try:
            # Get agent's offer
            context = self._build_turn_context()
            offer_output = await agent.make_offer(context)
            
            # Convert to our negotiation offer format
            negotiation_offer = self._convert_to_negotiation_offer(
                offer_output, agent_config.id, len(self.current_negotiation.turns) + 1
            )
            
            # Validate offer against ZOPA
            zopa_compliance = self._validate_offer_against_zopa(negotiation_offer)
            
            # Create turn record
            processing_time = (datetime.now() - start_time).total_seconds()
            turn = NegotiationTurn(
                turn_number=len(self.current_negotiation.turns) + 1,
                agent_id=agent_config.id,
                turn_type=TurnType.OFFER,
                offer=negotiation_offer,
                message=offer_output.message,
                zopa_compliance=zopa_compliance,
                processing_time=processing_time
            )
            
            # Add turn to negotiation
            self.current_negotiation.add_turn(turn)
            
            if verbose:
                self._print_turn_summary(turn, offer_output)
            
        except Exception as e:
            logger.error(f"Error executing turn for {agent_config.name}: {e}")
            raise
    
    def _build_turn_context(self) -> str:
        """Build context for the current turn."""
        context_parts = []
        
        # Add round information
        context_parts.append(f"This is round {self.current_negotiation.current_round} of {self.current_negotiation.max_rounds}.")
        
        # Add recent history if available
        if self.current_negotiation.offers:
            latest_offers = self.current_negotiation.get_latest_offers()
            if any(latest_offers.values()):
                context_parts.append("Consider the recent offers when making your decision.")
        
        # Add urgency if nearing end
        if self.current_negotiation.current_round > self.current_negotiation.max_rounds * 0.8:
            context_parts.append("The negotiation is nearing its end - consider making concessions if needed.")
        
        return " ".join(context_parts)
    
    def _convert_to_negotiation_offer(
        self, 
        offer_output: NegotiationOfferOutput, 
        agent_id: str, 
        turn_number: int
    ) -> NegotiationOffer:
        """Convert OpenAI agent output to our negotiation offer format."""
        return NegotiationOffer(
            agent_id=agent_id,
            turn_number=turn_number,
            volume=offer_output.volume,
            price=offer_output.price,
            payment_terms=offer_output.payment_terms,
            contract_duration=offer_output.contract_duration,
            message=offer_output.message,
            confidence=offer_output.confidence,
            reasoning=offer_output.reasoning
        )
    
    def _validate_offer_against_zopa(self, offer: NegotiationOffer) -> Dict[str, bool]:
        """Validate an offer against ZOPA boundaries."""
        return offer.is_within_zopa(self.current_negotiation.dimensions)
    
    def _print_zopa_analysis(self, dimensions: List[NegotiationDimension]) -> None:
        """Print ZOPA analysis for the negotiation."""
        print("\n" + "="*60)
        print("ZOPA ANALYSIS")
        print("="*60)
        
        for dim in dimensions:
            print(f"\n{dim.name.value.upper()}:")
            print(f"  Agent 1 range: {dim.agent1_min} - {dim.agent1_max} {dim.unit}")
            print(f"  Agent 2 range: {dim.agent2_min} - {dim.agent2_max} {dim.unit}")
            
            if dim.has_overlap():
                overlap = dim.get_overlap_range()
                print(f"  ✅ OVERLAP: {overlap[0]} - {overlap[1]} {dim.unit}")
            else:
                print(f"  ❌ NO OVERLAP - Negotiation will be challenging")
    
    def _print_turn_summary(self, turn: NegotiationTurn, offer_output: NegotiationOfferOutput) -> None:
        """Print a summary of the turn."""
        offer = turn.offer
        print(f"💼 Offer: {offer.volume} units @ ${offer.price}/unit")
        print(f"📅 Terms: {offer.payment_terms} days payment, {offer.contract_duration} months")
        print(f"💰 Total Value: ${offer.calculate_total_value():,.2f}")
        print(f"🎯 Confidence: {offer.confidence:.1%}")
        print(f"💬 Message: \"{offer.message}\"")
        print(f"🧠 Reasoning: {offer_output.reasoning}")
        
        # Show ZOPA compliance
        if turn.zopa_compliance:
            compliant_dims = [dim for dim, compliant in turn.zopa_compliance.items() if compliant]
            non_compliant_dims = [dim for dim, compliant in turn.zopa_compliance.items() if not compliant]
            
            if compliant_dims:
                print(f"✅ ZOPA compliant: {', '.join(compliant_dims)}")
            if non_compliant_dims:
                print(f"❌ ZOPA violations: {', '.join(non_compliant_dims)}")
    
    def _print_final_results(self, result) -> None:
        """Print final negotiation results."""
        print("\n" + "="*60)
        print("FINAL NEGOTIATION RESULTS")
        print("="*60)
        
        print(f"Status: {result.status.value}")
        print(f"Total turns: {result.total_turns}")
        print(f"Duration: {result.duration_seconds:.1f} seconds")
        
        if result.agreement_reached and result.final_agreement:
            print("\n🎉 AGREEMENT REACHED!")
            agreement = result.final_agreement
            print(f"📦 Volume: {agreement['volume']} units")
            print(f"💰 Price: ${agreement['price']}/unit")
            print(f"📅 Payment: {agreement['payment_terms']} days")
            print(f"⏰ Duration: {agreement['contract_duration']} months")
            print(f"💵 Total Value: ${agreement['volume'] * agreement['price']:,.2f}")
        else:
            print(f"\n❌ No agreement reached")
            if result.failure_reason:
                print(f"Reason: {result.failure_reason}")
        
        print(f"\n📊 Success Score: {result.get_success_score():.1%}")
    
    def get_negotiation_summary(self) -> Optional[Dict]:
        """Get a summary of the current/last negotiation."""
        if not self.current_negotiation:
            return None
        
        return {
            "negotiation_id": self.current_negotiation.id,
            "status": self.current_negotiation.status.value,
            "current_round": self.current_negotiation.current_round,
            "max_rounds": self.current_negotiation.max_rounds,
            "total_turns": len(self.current_negotiation.turns),
            "total_offers": len(self.current_negotiation.offers),
            "agreement_reached": self.current_negotiation.check_agreement(),
            "dimensions": [dim.name.value for dim in self.current_negotiation.dimensions]
        }
