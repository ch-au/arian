"""
CSV Import Utilities

This module provides utilities for importing negotiation tactics and other data from CSV files.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
import logging

from models.tactics import TacticLibrary, NegotiationTactic, TacticAspect, TacticType


logger = logging.getLogger(__name__)


class CSVImporter:
    """Utility class for importing data from CSV files."""
    
    @staticmethod
    def import_tactics_from_csv(csv_path: Path, library_description: Optional[str] = None) -> TacticLibrary:
        """
        Import negotiation tactics from a CSV file.
        
        Expected CSV format:
        Aspect,Influencing Techniques,Negotiation Tactics
        Focus,Persuading the person,Winning the negotiation
        
        Args:
            csv_path: Path to the CSV file
            library_description: Optional description for the tactic library
            
        Returns:
            TacticLibrary with imported tactics
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        library = TacticLibrary(
            description=library_description or f"Tactics imported from {csv_path.name}"
        )
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate required columns
                required_columns = {'Aspect', 'Influencing Techniques', 'Negotiation Tactics'}
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    raise ValueError(f"CSV must contain columns: {required_columns}")
                
                tactics_added = 0
                
                for row_idx, row in enumerate(reader, start=2):  # Start at 2 for header row
                    try:
                        aspect_str = row.get('Aspect', '').strip()
                        if not aspect_str:
                            logger.warning(f"Row {row_idx}: Empty aspect, skipping")
                            continue
                        
                        # Validate aspect
                        try:
                            aspect = TacticAspect(aspect_str)
                        except ValueError:
                            logger.warning(f"Row {row_idx}: Invalid aspect '{aspect_str}', skipping")
                            continue
                        
                        # Process influencing techniques
                        influencing = row.get('Influencing Techniques', '').strip()
                        if influencing:
                            tactic = CSVImporter._create_tactic(
                                aspect=aspect,
                                name=influencing,
                                tactic_type=TacticType.INFLUENCING,
                                row_idx=row_idx
                            )
                            library.add_tactic(tactic)
                            tactics_added += 1
                        
                        # Process negotiation tactics
                        negotiation = row.get('Negotiation Tactics', '').strip()
                        if negotiation:
                            tactic = CSVImporter._create_tactic(
                                aspect=aspect,
                                name=negotiation,
                                tactic_type=TacticType.NEGOTIATION,
                                row_idx=row_idx
                            )
                            library.add_tactic(tactic)
                            tactics_added += 1
                            
                    except Exception as e:
                        logger.error(f"Row {row_idx}: Error processing row - {e}")
                        continue
                
                logger.info(f"Successfully imported {tactics_added} tactics from {csv_path}")
                
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
        
        return library
    
    @staticmethod
    def _create_tactic(aspect: TacticAspect, name: str, tactic_type: TacticType, row_idx: int) -> NegotiationTactic:
        """Create a NegotiationTactic from CSV data."""
        
        # Generate unique ID
        type_prefix = "inf" if tactic_type == TacticType.INFLUENCING else "neg"
        tactic_id = f"{type_prefix}_{aspect.value.lower()}_{row_idx}"
        
        # Create description
        description = f"{tactic_type.value} focused on {aspect.value.lower()}: {name}"
        
        # Create prompt modifier based on aspect and type
        prompt_modifier = CSVImporter._generate_prompt_modifier(aspect, name, tactic_type)
        
        # Set default personality affinities and risk levels based on aspect
        personality_affinity = CSVImporter._get_default_personality_affinity(aspect, tactic_type)
        risk_level = CSVImporter._get_default_risk_level(aspect, tactic_type)
        effectiveness_weight = CSVImporter._get_default_effectiveness(aspect, tactic_type)
        
        return NegotiationTactic(
            id=tactic_id,
            name=name,
            aspect=aspect,
            tactic_type=tactic_type,
            description=description,
            prompt_modifier=prompt_modifier,
            personality_affinity=personality_affinity,
            risk_level=risk_level,
            effectiveness_weight=effectiveness_weight
        )
    
    @staticmethod
    def _generate_prompt_modifier(aspect: TacticAspect, name: str, tactic_type: TacticType) -> str:
        """Generate appropriate prompt modifier based on tactic characteristics."""
        
        base_instruction = f"Apply {name.lower()} approach"
        
        if aspect == TacticAspect.FOCUS:
            if tactic_type == TacticType.INFLUENCING:
                return f"{base_instruction} by focusing on building rapport and understanding the other party's perspective."
            else:
                return f"{base_instruction} by maintaining clear focus on achieving your negotiation objectives."
        
        elif aspect == TacticAspect.APPROACH:
            if tactic_type == TacticType.INFLUENCING:
                return f"{base_instruction} using psychological insights and relationship-building techniques."
            else:
                return f"{base_instruction} with strategic positioning and tactical maneuvering."
        
        elif aspect == TacticAspect.TIMING:
            if tactic_type == TacticType.INFLUENCING:
                return f"{base_instruction} by carefully timing your influence attempts for maximum impact."
            else:
                return f"{base_instruction} by strategically timing your moves during the negotiation."
        
        elif aspect == TacticAspect.TONE:
            if tactic_type == TacticType.INFLUENCING:
                return f"{base_instruction} while maintaining a cooperative and collaborative tone."
            else:
                return f"{base_instruction} with appropriate assertiveness and competitive edge when needed."
        
        elif aspect == TacticAspect.RISK:
            if tactic_type == TacticType.INFLUENCING:
                return f"{base_instruction} while being genuine and minimizing risk of appearing manipulative."
            else:
                return f"{base_instruction} while carefully managing the risks of aggressive tactics."
        
        else:
            return f"{base_instruction} with emphasis on {aspect.value.lower()}."
    
    @staticmethod
    def _get_default_personality_affinity(aspect: TacticAspect, tactic_type: TacticType) -> Dict[str, float]:
        """Get default personality trait affinities for a tactic."""
        
        # Base affinities for different aspects
        affinities = {}
        
        if aspect == TacticAspect.FOCUS:
            if tactic_type == TacticType.INFLUENCING:
                affinities = {"agreeableness": 0.7, "openness": 0.6}
            else:
                affinities = {"conscientiousness": 0.7, "extraversion": 0.6}
        
        elif aspect == TacticAspect.APPROACH:
            if tactic_type == TacticType.INFLUENCING:
                affinities = {"agreeableness": 0.8, "openness": 0.7, "extraversion": 0.6}
            else:
                affinities = {"extraversion": 0.7, "conscientiousness": 0.6, "neuroticism": 0.3}
        
        elif aspect == TacticAspect.TIMING:
            affinities = {"conscientiousness": 0.7, "openness": 0.5}
        
        elif aspect == TacticAspect.TONE:
            if tactic_type == TacticType.INFLUENCING:
                affinities = {"agreeableness": 0.8, "extraversion": 0.6}
            else:
                affinities = {"extraversion": 0.7, "agreeableness": 0.3, "neuroticism": 0.4}
        
        elif aspect == TacticAspect.RISK:
            if tactic_type == TacticType.INFLUENCING:
                affinities = {"agreeableness": 0.7, "conscientiousness": 0.6, "neuroticism": 0.3}
            else:
                affinities = {"extraversion": 0.6, "neuroticism": 0.6, "agreeableness": 0.2}
        
        return affinities
    
    @staticmethod
    def _get_default_risk_level(aspect: TacticAspect, tactic_type: TacticType) -> float:
        """Get default risk level for a tactic."""
        
        # Influencing techniques are generally lower risk
        if tactic_type == TacticType.INFLUENCING:
            base_risk = 0.3
        else:
            base_risk = 0.6
        
        # Adjust based on aspect
        if aspect == TacticAspect.TONE and tactic_type == TacticType.NEGOTIATION:
            return 0.7  # Competitive/aggressive tone is higher risk
        elif aspect == TacticAspect.RISK:
            return 0.8 if tactic_type == TacticType.NEGOTIATION else 0.2
        elif aspect == TacticAspect.APPROACH and tactic_type == TacticType.NEGOTIATION:
            return 0.7  # Strategic positioning can be risky
        
        return base_risk
    
    @staticmethod
    def _get_default_effectiveness(aspect: TacticAspect, tactic_type: TacticType) -> float:
        """Get default effectiveness weight for a tactic."""
        
        # Most tactics start with baseline effectiveness
        base_effectiveness = 1.0
        
        # Adjust based on aspect and type
        if aspect == TacticAspect.FOCUS:
            return 1.1  # Focus is generally effective
        elif aspect == TacticAspect.APPROACH and tactic_type == TacticType.INFLUENCING:
            return 1.2  # Relationship-building is highly effective
        elif aspect == TacticAspect.RISK and tactic_type == TacticType.NEGOTIATION:
            return 0.9  # High-risk tactics are less reliable
        
        return base_effectiveness
    
    @staticmethod
    def export_tactics_to_csv(library: TacticLibrary, csv_path: Path) -> None:
        """
        Export a tactic library to CSV format.
        
        Args:
            library: TacticLibrary to export
            csv_path: Path where to save the CSV file
        """
        # Group tactics by aspect and type
        export_data = {}
        
        for tactic in library.tactics:
            aspect = tactic.aspect.value
            if aspect not in export_data:
                export_data[aspect] = {
                    'Aspect': aspect,
                    'Influencing Techniques': '',
                    'Negotiation Tactics': ''
                }
            
            if tactic.tactic_type == TacticType.INFLUENCING:
                export_data[aspect]['Influencing Techniques'] = tactic.name
            else:
                export_data[aspect]['Negotiation Tactics'] = tactic.name
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['Aspect', 'Influencing Techniques', 'Negotiation Tactics']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for row_data in export_data.values():
                writer.writerow(row_data)
        
        logger.info(f"Exported {len(library.tactics)} tactics to {csv_path}")
    
    @staticmethod
    def validate_csv_format(csv_path: Path) -> Dict[str, Any]:
        """
        Validate the format of a tactics CSV file.
        
        Args:
            csv_path: Path to the CSV file to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'row_count': 0,
            'tactic_count': 0
        }
        
        try:
            if not csv_path.exists():
                validation_result['errors'].append(f"File not found: {csv_path}")
                return validation_result
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check required columns
                required_columns = {'Aspect', 'Influencing Techniques', 'Negotiation Tactics'}
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    validation_result['errors'].append(f"Missing required columns: {required_columns}")
                    return validation_result
                
                valid_aspects = {aspect.value for aspect in TacticAspect}
                
                for row_idx, row in enumerate(reader, start=2):
                    validation_result['row_count'] += 1
                    
                    aspect = row.get('Aspect', '').strip()
                    if not aspect:
                        validation_result['warnings'].append(f"Row {row_idx}: Empty aspect")
                        continue
                    
                    if aspect not in valid_aspects:
                        validation_result['errors'].append(f"Row {row_idx}: Invalid aspect '{aspect}'")
                        continue
                    
                    # Count tactics
                    if row.get('Influencing Techniques', '').strip():
                        validation_result['tactic_count'] += 1
                    if row.get('Negotiation Tactics', '').strip():
                        validation_result['tactic_count'] += 1
                
                validation_result['is_valid'] = len(validation_result['errors']) == 0
                
        except Exception as e:
            validation_result['errors'].append(f"Error reading file: {e}")
        
        return validation_result
