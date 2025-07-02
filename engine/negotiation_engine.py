"""
Negotiation Engine

This module contains the main orchestrator for negotiation simulations.
It coordinates between agents, manages the negotiation flow, and handles state persistence.
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
import logging
import asyncio
import time
from pathlib import Path

from models.agent import AgentConfig
from models.negotiation import (
    NegotiationState, 
    NegotiationDimension, 
    NegotiationOffer,
    NegotiationTurn,
    NegotiationResult,
    NegotiationStatus,
    TurnType,
    DimensionType
)
from models.zopa import ZOPAAnalysis
from utils.validators import validate_negotiation_setup
from utils.config_manager import ConfigManager
from .turn_manager import TurnManager
from .zopa_validator import ZOPAValidator
from .agreement_detector import AgreementDetector
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class NegotiationEngine:
    """
    Main orchestrator for negotiation simulations.
    
    Coordinates the entire negotiation process from setup to completion,
    managing agent interactions, state persistence, and result analysis.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the negotiation engine.
        
        Args:
            config_manager: Configuration manager for persistence
        """
        self.config_manager = config_manager
        self.turn_manager = TurnManager()
        self.zopa_validator = ZOPAValidator()
        self.agreement_detector = AgreementDetector()
        self.state_manager = StateManager(config_manager)
        
        # Event callbacks
        self.on_turn_completed: Optional[Callable[[NegotiationTurn], None]] = None
        self.on_offer_made: Optional[Callable[[NegotiationOffer], None]] = None
        self.on_agreement_reached: Optional[Callable[[NegotiationResult], None]] = None
        self.on_negotiation_failed: Optional[Callable[[NegotiationResult], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
    
    def create_negotiation(
        self,
        agent1_config: AgentConfig,
        agent2_config: AgentConfig,
        max_rounds: int = 20,
        auto_save: bool = True
    ) -> NegotiationState:
        """
        Create a new negotiation between two agents.
        
        Args:
            agent1_config: Configuration for the first agent
            agent2_config: Configuration for the second agent
            max_rounds: Maximum number of negotiation rounds
            auto_save: Whether to automatically save state changes
            
        Returns:
            Initialized negotiation state
            
        Raises:
            ValueError: If the negotiation setup is invalid
        """
        # Validate the setup
        validation_result = validate_negotiation_setup(
            agent1_config, agent2_config, max_rounds
        )
        
        if not validation_result['is_valid']:
            error_msg = f"Invalid negotiation setup: {validation_result['errors']}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create negotiation dimensions from agent ZOPA boundaries
        dimensions = self._create_dimensions_from_agents(agent1_config, agent2_config)
        
        # Create negotiation state
        negotiation = NegotiationState(
            agent1_id=agent1_config.id,
            agent2_id=agent2_config.id,
            max_rounds=max_rounds,
            dimensions=dimensions
        )
        
        # Save initial state if auto_save is enabled
        if auto_save:
            self.state_manager.save_negotiation_state(negotiation)
        
        logger.info(f"Created negotiation {negotiation.id} between {agent1_config.name} and {agent2_config.name}")
        return negotiation
    
    def _create_dimensions_from_agents(
        self, 
        agent1_config: AgentConfig, 
        agent2_config: AgentConfig
    ) -> List[NegotiationDimension]:
        """Create negotiation dimensions from agent ZOPA boundaries."""
        dimensions = []
        
        # Standard dimension configurations
        dimension_configs = {
            DimensionType.VOLUME: {"unit": "units"},
            DimensionType.PRICE: {"unit": "$/unit"},
            DimensionType.PAYMENT_TERMS: {"unit": "days"},
            DimensionType.CONTRACT_DURATION: {"unit": "months"}
        }
        
        for dim_type, config in dimension_configs.items():
            dim_name = dim_type.value
            
            # Get ZOPA boundaries from both agents
            agent1_zopa = agent1_config.get_zopa_for_dimension(dim_name)
            agent2_zopa = agent2_config.get_zopa_for_dimension(dim_name)
            
            if agent1_zopa and agent2_zopa:
                dimension = NegotiationDimension(
                    name=dim_type,
                    unit=config["unit"],
                    agent1_min=agent1_zopa['min_acceptable'],
                    agent1_max=agent1_zopa['max_desired'],
                    agent2_min=agent2_zopa['min_acceptable'],
                    agent2_max=agent2_zopa['max_desired']
                )
                dimensions.append(dimension)
        
        return dimensions
    
    async def run_negotiation(
        self,
        negotiation: NegotiationState,
        agent1_config: AgentConfig,
        agent2_config: AgentConfig,
        agent_callback: Callable[[str, AgentConfig, NegotiationState], NegotiationOffer]
    ) -> NegotiationResult:
        """
        Run a complete negotiation simulation.
        
        Args:
            negotiation: The negotiation state to run
            agent1_config: Configuration for agent 1
            agent2_config: Configuration for agent 2
            agent_callback: Function to get agent responses
            
        Returns:
            Final negotiation result
        """
        try:
            # Start the negotiation
            negotiation.start_negotiation()
            logger.info(f"Started negotiation {negotiation.id}")
            
            # Main negotiation loop
            while True:
                # Check termination conditions
                should_terminate, reason = negotiation.should_terminate()
                if should_terminate:
                    logger.info(f"Negotiation {negotiation.id} terminating: {reason}")
                    break
                
                # Get current agent configuration
                current_agent_id = negotiation.current_turn_agent
                if current_agent_id == agent1_config.id:
                    current_agent_config = agent1_config
                else:
                    current_agent_config = agent2_config
                
                # Execute turn
                await self._execute_turn(
                    negotiation, 
                    current_agent_config, 
                    agent_callback
                )
                
                # Save state after each turn
                self.state_manager.save_negotiation_state(negotiation)
            
            # Finalize negotiation
            result = negotiation.finalize_negotiation(reason)
            
            # Trigger appropriate callback
            if result.agreement_reached and self.on_agreement_reached:
                self.on_agreement_reached(result)
            elif not result.agreement_reached and self.on_negotiation_failed:
                self.on_negotiation_failed(result)
            
            logger.info(f"Negotiation {negotiation.id} completed with status: {result.status.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error during negotiation {negotiation.id}: {e}")
            if self.on_error:
                self.on_error(e)
            
            # Mark negotiation as failed due to error
            negotiation.status = NegotiationStatus.FAILED_ERROR
            result = negotiation.finalize_negotiation("error")
            result.failure_reason = str(e)
            return result
    
    async def _execute_turn(
        self,
        negotiation: NegotiationState,
        agent_config: AgentConfig,
        agent_callback: Callable[[str, AgentConfig, NegotiationState], NegotiationOffer]
    ) -> None:
        """Execute a single turn in the negotiation."""
        start_time = time.time()
        
        try:
            # Get agent's offer
            offer = await asyncio.get_event_loop().run_in_executor(
                None, agent_callback, agent_config.id, agent_config, negotiation
            )
            
            # Validate offer against ZOPA
            zopa_compliance = self.zopa_validator.validate_offer(offer, negotiation.dimensions)
            
            # Calculate concessions if this isn't the first offer
            concession_analysis = self._analyze_concessions(negotiation, offer)
            
            # Create turn record
            turn = NegotiationTurn(
                turn_number=len(negotiation.turns) + 1,
                agent_id=agent_config.id,
                turn_type=TurnType.OFFER,
                offer=offer,
                message=offer.message,
                zopa_compliance=zopa_compliance,
                concession_analysis=concession_analysis,
                processing_time=time.time() - start_time
            )
            
            # Add turn to negotiation
            negotiation.add_turn(turn)
            
            # Trigger callbacks
            if self.on_turn_completed:
                self.on_turn_completed(turn)
            if self.on_offer_made:
                self.on_offer_made(offer)
            
            logger.debug(f"Turn {turn.turn_number} completed by {agent_config.name}")
            
        except Exception as e:
            logger.error(f"Error executing turn for {agent_config.name}: {e}")
            raise
    
    def _analyze_concessions(
        self, 
        negotiation: NegotiationState, 
        current_offer: NegotiationOffer
    ) -> Dict[str, float]:
        """Analyze concessions made in the current offer compared to previous offers."""
        concessions = {}
        
        # Get previous offer from the same agent
        previous_offer = None
        for offer in reversed(negotiation.offers):
            if offer.agent_id == current_offer.agent_id:
                previous_offer = offer
                break
        
        if not previous_offer:
            return concessions  # No previous offer to compare
        
        # Calculate concessions for each dimension
        current_values = current_offer.to_dict()
        previous_values = previous_offer.to_dict()
        
        for dimension_name, current_value in current_values.items():
            if dimension_name in previous_values:
                previous_value = previous_values[dimension_name]
                
                # Calculate percentage change
                if previous_value != 0:
                    change = (current_value - previous_value) / previous_value
                    concessions[dimension_name] = change
                else:
                    concessions[dimension_name] = 0.0
        
        return concessions
    
    def get_negotiation_analysis(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """
        Get comprehensive analysis of a negotiation.
        
        Args:
            negotiation: The negotiation to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'basic_info': negotiation.get_summary(),
            'zopa_analysis': None,
            'turn_analysis': self._analyze_turns(negotiation),
            'offer_analysis': self._analyze_offers(negotiation),
            'communication_analysis': self._analyze_communication(negotiation)
        }
        
        # Add ZOPA analysis if we have agent configs
        try:
            agent1_config = self.config_manager.load_agent_config(negotiation.agent1_id)
            agent2_config = self.config_manager.load_agent_config(negotiation.agent2_id)
            
            if agent1_config and agent2_config:
                zopa_analysis = ZOPAAnalysis.from_agent_configs(
                    negotiation.id, agent1_config, agent2_config
                )
                analysis['zopa_analysis'] = zopa_analysis.get_summary_report()
        except Exception as e:
            logger.warning(f"Could not generate ZOPA analysis: {e}")
        
        return analysis
    
    def _analyze_turns(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """Analyze turn patterns and timing."""
        if not negotiation.turns:
            return {}
        
        processing_times = [turn.processing_time for turn in negotiation.turns if turn.processing_time]
        
        return {
            'total_turns': len(negotiation.turns),
            'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
            'max_processing_time': max(processing_times) if processing_times else 0,
            'turn_types': {
                turn_type.value: sum(1 for turn in negotiation.turns if turn.turn_type == turn_type)
                for turn_type in TurnType
            }
        }
    
    def _analyze_offers(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """Analyze offer patterns and convergence."""
        if not negotiation.offers:
            return {}
        
        # Group offers by agent
        agent1_offers = [offer for offer in negotiation.offers if offer.agent_id == negotiation.agent1_id]
        agent2_offers = [offer for offer in negotiation.offers if offer.agent_id == negotiation.agent2_id]
        
        analysis = {
            'total_offers': len(negotiation.offers),
            'agent1_offers': len(agent1_offers),
            'agent2_offers': len(agent2_offers),
            'convergence_analysis': {}
        }
        
        # Analyze convergence for each dimension
        if len(agent1_offers) > 1 and len(agent2_offers) > 1:
            dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
            
            for dimension in dimensions:
                agent1_values = [getattr(offer, dimension) for offer in agent1_offers]
                agent2_values = [getattr(offer, dimension) for offer in agent2_offers]
                
                # Calculate convergence (decreasing distance between offers)
                if len(agent1_values) >= 2 and len(agent2_values) >= 2:
                    initial_distance = abs(agent1_values[0] - agent2_values[0])
                    final_distance = abs(agent1_values[-1] - agent2_values[-1])
                    
                    convergence = (initial_distance - final_distance) / initial_distance if initial_distance > 0 else 0
                    analysis['convergence_analysis'][dimension] = convergence
        
        return analysis
    
    def _analyze_communication(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """Analyze communication patterns."""
        if not negotiation.turns:
            return {}
        
        messages = [turn.message for turn in negotiation.turns if turn.message]
        message_lengths = [len(message.split()) for message in messages]
        
        return {
            'total_messages': len(messages),
            'avg_message_length': sum(message_lengths) / len(message_lengths) if message_lengths else 0,
            'total_words': sum(message_lengths),
            'communication_frequency': len(messages) / len(negotiation.turns) if negotiation.turns else 0
        }
    
    def resume_negotiation(
        self,
        negotiation_id: str,
        agent1_config: AgentConfig,
        agent2_config: AgentConfig,
        agent_callback: Callable[[str, AgentConfig, NegotiationState], NegotiationOffer]
    ) -> Optional[NegotiationResult]:
        """
        Resume a previously saved negotiation.
        
        Args:
            negotiation_id: ID of the negotiation to resume
            agent1_config: Configuration for agent 1
            agent2_config: Configuration for agent 2
            agent_callback: Function to get agent responses
            
        Returns:
            Final negotiation result if successful, None if negotiation not found
        """
        negotiation = self.state_manager.load_negotiation_state(negotiation_id)
        if not negotiation:
            logger.error(f"Negotiation {negotiation_id} not found")
            return None
        
        if negotiation.status != NegotiationStatus.IN_PROGRESS:
            logger.warning(f"Negotiation {negotiation_id} is not in progress (status: {negotiation.status})")
            return negotiation.result
        
        logger.info(f"Resuming negotiation {negotiation_id}")
        return asyncio.run(self.run_negotiation(negotiation, agent1_config, agent2_config, agent_callback))
    
    def get_negotiation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of recent negotiations.
        
        Args:
            limit: Maximum number of negotiations to return
            
        Returns:
            List of negotiation summaries
        """
        return self.config_manager.list_negotiations()[:limit]
