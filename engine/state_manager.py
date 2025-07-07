"""
State Manager

This module manages the persistence and state tracking of negotiations,
ensuring data integrity and providing state recovery capabilities.
"""

from typing import Dict, List, Optional, Any
import logging
import json
from pathlib import Path
from datetime import datetime

from models.negotiation import NegotiationState, NegotiationStatus
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages negotiation state persistence and recovery.
    
    Handles saving, loading, and tracking of negotiation states,
    ensuring data integrity and providing recovery capabilities.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the state manager.
        
        Args:
            config_manager: Configuration manager for persistence
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Cache for frequently accessed states
        self._state_cache = {}
        self._cache_max_size = 10
    
    def save_negotiation_state(self, negotiation: NegotiationState) -> bool:
        """
        Save a negotiation state to persistent storage.
        
        Args:
            negotiation: The negotiation state to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Update cache
            self._update_cache(negotiation)
            
            # Save to persistent storage
            self.config_manager.save_negotiation_state(negotiation)
            
            self.logger.debug(f"Saved negotiation state: {negotiation.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save negotiation state {negotiation.id}: {e}")
            return False
    
    def load_negotiation_state(self, negotiation_id: str) -> Optional[NegotiationState]:
        """
        Load a negotiation state from storage.
        
        Args:
            negotiation_id: ID of the negotiation to load
            
        Returns:
            NegotiationState if found, None otherwise
        """
        # Check cache first
        if negotiation_id in self._state_cache:
            self.logger.debug(f"Loaded negotiation state from cache: {negotiation_id}")
            return self._state_cache[negotiation_id]
        
        # Load from persistent storage
        try:
            negotiation = self.config_manager.load_negotiation_state(negotiation_id)
            
            if negotiation:
                # Add to cache
                self._update_cache(negotiation)
                self.logger.debug(f"Loaded negotiation state from storage: {negotiation_id}")
            
            return negotiation
            
        except Exception as e:
            self.logger.error(f"Failed to load negotiation state {negotiation_id}: {e}")
            return None
    
    def _update_cache(self, negotiation: NegotiationState) -> None:
        """Update the state cache with the given negotiation."""
        # Remove oldest entry if cache is full
        if len(self._state_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._state_cache))
            del self._state_cache[oldest_key]
        
        # Add/update the negotiation
        self._state_cache[negotiation.id] = negotiation
    
    def create_checkpoint(self, negotiation: NegotiationState, checkpoint_name: str = None) -> str:
        """
        Create a checkpoint of the current negotiation state.
        
        Args:
            negotiation: The negotiation to checkpoint
            checkpoint_name: Optional name for the checkpoint
            
        Returns:
            Checkpoint ID
        """
        if not checkpoint_name:
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        checkpoint_id = f"{negotiation.id}_{checkpoint_name}"
        
        try:
            # Create a copy of the negotiation with checkpoint ID
            checkpoint_data = negotiation.dict()
            checkpoint_data['id'] = checkpoint_id
            checkpoint_data['checkpoint_info'] = {
                'original_id': negotiation.id,
                'checkpoint_name': checkpoint_name,
                'created_at': datetime.now().isoformat(),
                'original_status': negotiation.status.value,
                'turn_count': len(negotiation.turns),
                'offer_count': len(negotiation.offers)
            }
            
            # Save checkpoint
            checkpoint_path = self.config_manager.negotiations_path / f"checkpoint_{checkpoint_id}.json"
            with open(checkpoint_path, 'w', encoding='utf-8') as file:
                json.dump(checkpoint_data, file, indent=2, default=str)
            
            self.logger.info(f"Created checkpoint {checkpoint_id} for negotiation {negotiation.id}")
            return checkpoint_id
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint for negotiation {negotiation.id}: {e}")
            raise
    
    def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[NegotiationState]:
        """
        Restore a negotiation from a checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to restore
            
        Returns:
            Restored negotiation state if successful, None otherwise
        """
        try:
            checkpoint_path = self.config_manager.negotiations_path / f"checkpoint_{checkpoint_id}.json"
            
            if not checkpoint_path.exists():
                self.logger.error(f"Checkpoint not found: {checkpoint_id}")
                return None
            
            with open(checkpoint_path, 'r', encoding='utf-8') as file:
                checkpoint_data = json.load(file)
            
            # Restore original ID
            if 'checkpoint_info' in checkpoint_data:
                original_id = checkpoint_data['checkpoint_info']['original_id']
                checkpoint_data['id'] = original_id
                del checkpoint_data['checkpoint_info']
            
            # Create negotiation state
            negotiation = NegotiationState(**checkpoint_data)
            
            # Update cache
            self._update_cache(negotiation)
            
            self.logger.info(f"Restored negotiation {negotiation.id} from checkpoint {checkpoint_id}")
            return negotiation
            
        except Exception as e:
            self.logger.error(f"Failed to restore from checkpoint {checkpoint_id}: {e}")
            return None
    
    def list_checkpoints(self, negotiation_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a specific negotiation.
        
        Args:
            negotiation_id: ID of the negotiation
            
        Returns:
            List of checkpoint information
        """
        checkpoints = []
        
        try:
            checkpoint_pattern = f"checkpoint_{negotiation_id}_*.json"
            checkpoint_files = list(self.config_manager.negotiations_path.glob(checkpoint_pattern))
            
            for checkpoint_file in checkpoint_files:
                try:
                    with open(checkpoint_file, 'r', encoding='utf-8') as file:
                        checkpoint_data = json.load(file)
                    
                    if 'checkpoint_info' in checkpoint_data:
                        info = checkpoint_data['checkpoint_info']
                        checkpoints.append({
                            'checkpoint_id': checkpoint_data['id'],
                            'checkpoint_name': info['checkpoint_name'],
                            'created_at': info['created_at'],
                            'original_status': info['original_status'],
                            'turn_count': info['turn_count'],
                            'offer_count': info['offer_count'],
                            'file_path': str(checkpoint_file)
                        })
                
                except Exception as e:
                    self.logger.warning(f"Failed to read checkpoint file {checkpoint_file}: {e}")
                    continue
            
            # Sort by creation date (newest first)
            checkpoints.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list checkpoints for negotiation {negotiation_id}: {e}")
        
        return checkpoints
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a specific checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            checkpoint_path = self.config_manager.negotiations_path / f"checkpoint_{checkpoint_id}.json"
            
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                self.logger.info(f"Deleted checkpoint: {checkpoint_id}")
                return True
            else:
                self.logger.warning(f"Checkpoint not found for deletion: {checkpoint_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False
    
    def get_negotiation_history(self, negotiation_id: str) -> Dict[str, Any]:
        """
        Get the complete history of a negotiation including checkpoints.
        
        Args:
            negotiation_id: ID of the negotiation
            
        Returns:
            Dictionary with negotiation history
        """
        history = {
            'negotiation_id': negotiation_id,
            'current_state': None,
            'checkpoints': [],
            'state_changes': [],
            'statistics': {}
        }
        
        try:
            # Load current state
            current_state = self.load_negotiation_state(negotiation_id)
            if current_state:
                history['current_state'] = current_state.get_summary()
            
            # Load checkpoints
            history['checkpoints'] = self.list_checkpoints(negotiation_id)
            
            # Analyze state changes
            if current_state:
                history['state_changes'] = self._analyze_state_changes(current_state)
                history['statistics'] = self._calculate_negotiation_statistics(current_state)
            
        except Exception as e:
            self.logger.error(f"Failed to get negotiation history for {negotiation_id}: {e}")
        
        return history
    
    def _analyze_state_changes(self, negotiation: NegotiationState) -> List[Dict[str, Any]]:
        """Analyze significant state changes in the negotiation."""
        changes = []
        
        # Track status changes
        if negotiation.started_at:
            changes.append({
                'timestamp': negotiation.started_at.isoformat(),
                'type': 'status_change',
                'description': 'Negotiation started',
                'details': {'new_status': 'in_progress'}
            })
        
        # Track significant turns
        for turn in negotiation.turns:
            if turn.turn_type.value in ['acceptance', 'rejection', 'walk_away']:
                changes.append({
                    'timestamp': turn.timestamp.isoformat(),
                    'type': 'significant_turn',
                    'description': f"Agent {turn.agent_id} performed {turn.turn_type.value}",
                    'details': {
                        'turn_number': turn.turn_number,
                        'turn_type': turn.turn_type.value,
                        'agent_id': turn.agent_id
                    }
                })
        
        # Track final status
        if negotiation.ended_at:
            changes.append({
                'timestamp': negotiation.ended_at.isoformat(),
                'type': 'status_change',
                'description': f'Negotiation ended with status: {negotiation.status.value}',
                'details': {'final_status': negotiation.status.value}
            })
        
        return sorted(changes, key=lambda x: x['timestamp'])
    
    def _calculate_negotiation_statistics(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """Calculate statistics for the negotiation."""
        stats = {
            'duration_seconds': 0.0,
            'total_turns': len(negotiation.turns),
            'total_offers': len(negotiation.offers),
            'rounds_completed': negotiation.current_round,
            'agent_participation': {},
            'offer_frequency': {},
            'average_processing_time': 0.0
        }
        
        # Calculate duration
        if negotiation.started_at and negotiation.ended_at:
            duration = negotiation.ended_at - negotiation.started_at
            stats['duration_seconds'] = duration.total_seconds()
        
        # Agent participation
        agent_turns = {}
        agent_offers = {}
        
        for turn in negotiation.turns:
            agent_turns[turn.agent_id] = agent_turns.get(turn.agent_id, 0) + 1
        
        for offer in negotiation.offers:
            agent_offers[offer.agent_id] = agent_offers.get(offer.agent_id, 0) + 1
        
        stats['agent_participation'] = {
            'turns': agent_turns,
            'offers': agent_offers
        }
        
        # Processing time statistics
        processing_times = [turn.processing_time for turn in negotiation.turns if turn.processing_time]
        if processing_times:
            stats['average_processing_time'] = sum(processing_times) / len(processing_times)
            stats['max_processing_time'] = max(processing_times)
            stats['min_processing_time'] = min(processing_times)
        
        return stats
    
    def cleanup_old_states(self, days_old: int = 30) -> int:
        """
        Clean up old negotiation states and checkpoints.
        
        Args:
            days_old: Remove states older than this many days
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        try:
            # Clean up negotiation files
            for file_path in self.config_manager.negotiations_path.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_date:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        self.logger.debug(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete old file {file_path}: {e}")
            
            # Clear cache of old entries
            self._state_cache.clear()
            
            self.logger.info(f"Cleaned up {cleaned_count} old negotiation files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old states: {e}")
        
        return cleaned_count
    
    def validate_state_integrity(self, negotiation: NegotiationState) -> Dict[str, Any]:
        """
        Validate the integrity of a negotiation state.
        
        Args:
            negotiation: The negotiation state to validate
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # Check basic structure
            if not negotiation.id:
                validation['errors'].append("Missing negotiation ID")
                validation['is_valid'] = False
            
            if not negotiation.agent1_id or not negotiation.agent2_id:
                validation['errors'].append("Missing agent IDs")
                validation['is_valid'] = False
            
            # Check turn sequence
            expected_turn_number = 1
            for turn in negotiation.turns:
                if turn.turn_number != expected_turn_number:
                    validation['errors'].append(f"Turn sequence error: expected {expected_turn_number}, got {turn.turn_number}")
                    validation['is_valid'] = False
                expected_turn_number += 1
            
            # Check offer consistency
            for offer in negotiation.offers:
                if offer.agent_id not in [negotiation.agent1_id, negotiation.agent2_id]:
                    validation['errors'].append(f"Invalid agent ID in offer: {offer.agent_id}")
                    validation['is_valid'] = False
            
            # Check status consistency
            if negotiation.status == NegotiationStatus.IN_PROGRESS:
                if negotiation.ended_at:
                    validation['warnings'].append("Negotiation marked as in progress but has end time")
            elif negotiation.status != NegotiationStatus.SETUP:
                if not negotiation.ended_at:
                    validation['warnings'].append("Completed negotiation missing end time")
            
            # Calculate statistics
            validation['statistics'] = {
                'turn_count': len(negotiation.turns),
                'offer_count': len(negotiation.offers),
                'dimension_count': len(negotiation.dimensions),
                'current_round': negotiation.current_round,
                'max_rounds': negotiation.max_rounds
            }
            
        except Exception as e:
            validation['errors'].append(f"Validation error: {e}")
            validation['is_valid'] = False
        
        return validation
    
    def export_negotiation_data(self, negotiation_id: str, export_path: Path) -> bool:
        """
        Export complete negotiation data including history and checkpoints.
        
        Args:
            negotiation_id: ID of the negotiation to export
            export_path: Path where to save the export
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            # Get complete history
            history = self.get_negotiation_history(negotiation_id)
            
            # Load current state
            negotiation = self.load_negotiation_state(negotiation_id)
            if not negotiation:
                self.logger.error(f"Negotiation not found for export: {negotiation_id}")
                return False
            
            # Create export data
            export_data = {
                'export_info': {
                    'negotiation_id': negotiation_id,
                    'exported_at': datetime.now().isoformat(),
                    'export_version': '1.0'
                },
                'negotiation_state': negotiation.dict(),
                'history': history,
                'validation': self.validate_state_integrity(negotiation)
            }
            
            # Save export
            with open(export_path, 'w', encoding='utf-8') as file:
                json.dump(export_data, file, indent=2, default=str)
            
            self.logger.info(f"Exported negotiation data to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export negotiation data: {e}")
            return False
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all managed negotiation states.
        
        Returns:
            Dictionary with state management summary
        """
        summary = {
            'total_negotiations': 0,
            'active_negotiations': 0,
            'completed_negotiations': 0,
            'failed_negotiations': 0,
            'cache_size': len(self._state_cache),
            'storage_stats': {},
            'recent_activity': []
        }
        
        try:
            # Get storage statistics
            summary['storage_stats'] = self.config_manager.get_storage_stats()['negotiations']
            
            # Analyze negotiations
            negotiations = self.config_manager.list_negotiations()
            summary['total_negotiations'] = len(negotiations)
            
            for negotiation_summary in negotiations:
                status = negotiation_summary.get('status', '')
                if 'progress' in status:
                    summary['active_negotiations'] += 1
                elif 'agreement' in status or 'completed' in status:
                    summary['completed_negotiations'] += 1
                elif 'failed' in status:
                    summary['failed_negotiations'] += 1
            
            # Recent activity (last 5 negotiations)
            summary['recent_activity'] = negotiations[:5]
            
        except Exception as e:
            self.logger.error(f"Failed to generate state summary: {e}")
        
        return summary
