#!/usr/bin/env python3
"""
Negotiation Configuration Interface

A Streamlit-based web interface for configuring and running AI negotiations.
Provides forms for setting up negotiation context, agent personalities,
ZOPA boundaries, and tactics selection.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import json
import asyncio
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.context import NegotiationContext, HistoryType, ProductCategory, MarketCondition
from models.agent import AgentConfig, PersonalityProfile, PowerLevel
from models.negotiation import NegotiationDimension, DimensionType
from models.tactics import TacticType
# Note: CSVImporter not needed for interface functionality
# from utils.csv_importer import CSVImporter
try:
    from agents_openai.agent_factory import AgentFactory
    from agents_openai.negotiation_runner import NegotiationRunner
    OPENAI_AGENTS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    OPENAI_AGENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Create fallback classes for interface to work
    class AgentFactory:
        def __init__(self): pass
        def create_buyer_agent(self, **kwargs): return None
        def create_seller_agent(self, **kwargs): return None
        def create_negotiation_agent(self, **kwargs): return None
    
    class NegotiationRunner:
        def __init__(self, factory): pass
        async def run_negotiation(self, **kwargs): return None
        def get_negotiation_summary(self): return None


# Page configuration
st.set_page_config(
    page_title="AI Negotiation Configurator",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e8b57;
        border-bottom: 2px solid #2e8b57;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
    .agent-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .zopa-overlap {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .zopa-no-overlap {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'negotiation_context' not in st.session_state:
        st.session_state.negotiation_context = None
    if 'agent1_config' not in st.session_state:
        st.session_state.agent1_config = None
    if 'agent2_config' not in st.session_state:
        st.session_state.agent2_config = None
    if 'negotiation_results' not in st.session_state:
        st.session_state.negotiation_results = None
    if 'available_tactics' not in st.session_state:
        st.session_state.available_tactics = load_tactics()


def load_tactics() -> List[Dict[str, str]]:
    """Load available negotiation tactics."""
    # For now, return a predefined list. Later this can be loaded from CSV
    return [
        {
            "id": "collaborative",
            "name": "Collaborative",
            "category": "Influencing",
            "description": "Focus on mutual benefit and win-win solutions"
        },
        {
            "id": "competitive",
            "name": "Competitive",
            "category": "Strategic",
            "description": "Assertive approach focused on winning"
        },
        {
            "id": "anchoring",
            "name": "Anchoring",
            "category": "Strategic",
            "description": "Set initial reference points to influence perception"
        },
        {
            "id": "rapport_building",
            "name": "Rapport Building",
            "category": "Influencing",
            "description": "Build relationship and trust before negotiating"
        },
        {
            "id": "deadline_pressure",
            "name": "Deadline Pressure",
            "category": "Strategic",
            "description": "Use time constraints to create urgency"
        },
        {
            "id": "incremental_concession",
            "name": "Incremental Concession",
            "category": "Strategic",
            "description": "Make small, gradual concessions"
        }
    ]


def create_negotiation_context_form() -> Optional[NegotiationContext]:
    """Create form for negotiation context configuration."""
    st.markdown('<div class="section-header">📊 Negotiation Context</div>', unsafe_allow_html=True)
    
    with st.form("negotiation_context_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Product Information")
            product_name = st.text_input("Product Name", value="Premium Chocolate", help="Name of the product or service")
            product_group = st.text_input("Product Group", value="Sweets", help="Category or group (e.g., Sweets, Electronics)")
            product_category = st.selectbox("Product Category", options=[cat.value for cat in ProductCategory])
            
            st.subheader("Baseline Values")
            baseline_volume = st.number_input("Baseline Volume", min_value=1, value=3000, help="Current/baseline volume in units")
            baseline_price = st.number_input("Baseline Price ($/unit)", min_value=0.01, value=12.50, format="%.2f", help="Current/baseline price per unit")
            
        with col2:
            st.subheader("Negotiation History")
            history_type = st.selectbox("History Type", options=[hist.value for hist in HistoryType])
            
            if history_type != HistoryType.FIRST_CONTACT.value:
                relationship_duration = st.number_input("Relationship Duration (months)", min_value=0, value=24)
                previous_agreements = st.number_input("Previous Agreements", min_value=0, value=2)
            else:
                relationship_duration = None
                previous_agreements = None
            
            st.subheader("Market Context")
            market_condition = st.selectbox("Market Condition", options=[market.value for market in MarketCondition])
            urgency_level = st.slider("Urgency Level", min_value=0.0, max_value=1.0, value=0.5, help="0=No rush, 1=Very urgent")
        
        # Additional context
        st.subheader("Additional Context")
        col3, col4 = st.columns(2)
        with col3:
            baseline_payment_terms = st.number_input("Baseline Payment Terms (days)", min_value=0, max_value=365, value=30)
            baseline_contract_duration = st.number_input("Baseline Contract Duration (months)", min_value=1, max_value=120, value=12)
        with col4:
            market_notes = st.text_area("Market Notes", help="Additional market context")
            special_requirements = st.text_area("Special Requirements", help="Special requirements or considerations")
        
        submitted = st.form_submit_button("Save Context", type="primary")
        
        if submitted:
            try:
                context = NegotiationContext(
                    product_name=product_name,
                    product_group=product_group,
                    product_category=ProductCategory(product_category),
                    history_type=HistoryType(history_type),
                    previous_agreements=previous_agreements,
                    relationship_duration_months=relationship_duration,
                    baseline_volume=baseline_volume,
                    baseline_price=baseline_price,
                    baseline_payment_terms=baseline_payment_terms,
                    baseline_contract_duration=baseline_contract_duration,
                    market_condition=MarketCondition(market_condition),
                    market_notes=market_notes if market_notes else None,
                    urgency_level=urgency_level,
                    special_requirements=special_requirements if special_requirements else None
                )
                st.success("✅ Negotiation context saved successfully!")
                return context
            except Exception as e:
                st.error(f"❌ Error creating context: {str(e)}")
                return None
    
    return None


def create_personality_sliders(agent_name: str, default_values: Optional[Dict[str, float]] = None) -> PersonalityProfile:
    """Create personality trait sliders for an agent."""
    defaults = default_values or {}
    
    st.subheader(f"🧠 {agent_name} Personality (Big 5)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        openness = st.slider(
            "Openness to Experience",
            min_value=0.0, max_value=1.0, value=defaults.get('openness', 0.5), step=0.1,
            help="Creativity, curiosity, willingness to try new approaches",
            key=f"{agent_name}_openness"
        )
        
        conscientiousness = st.slider(
            "Conscientiousness",
            min_value=0.0, max_value=1.0, value=defaults.get('conscientiousness', 0.5), step=0.1,
            help="Organization, attention to detail, systematic approach",
            key=f"{agent_name}_conscientiousness"
        )
        
        extraversion = st.slider(
            "Extraversion",
            min_value=0.0, max_value=1.0, value=defaults.get('extraversion', 0.5), step=0.1,
            help="Assertiveness, social confidence, communication style",
            key=f"{agent_name}_extraversion"
        )
    
    with col2:
        agreeableness = st.slider(
            "Agreeableness",
            min_value=0.0, max_value=1.0, value=defaults.get('agreeableness', 0.5), step=0.1,
            help="Cooperation, trust, willingness to compromise",
            key=f"{agent_name}_agreeableness"
        )
        
        neuroticism = st.slider(
            "Neuroticism",
            min_value=0.0, max_value=1.0, value=defaults.get('neuroticism', 0.5), step=0.1,
            help="Emotional stability, stress response, risk tolerance",
            key=f"{agent_name}_neuroticism"
        )
    
    return PersonalityProfile(
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism
    )


def create_zopa_configuration(agent_name: str, context: NegotiationContext, default_values: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
    """Create ZOPA boundary configuration for an agent."""
    st.subheader(f"📊 {agent_name} ZOPA Boundaries")
    
    defaults = default_values or {}
    zopa_boundaries = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Volume (units)**")
        vol_min = st.number_input(
            f"Min Acceptable Volume",
            min_value=1, value=defaults.get('volume', {}).get('min_acceptable', context.baseline_volume // 2),
            key=f"{agent_name}_vol_min"
        )
        vol_max = st.number_input(
            f"Max Desired Volume",
            min_value=vol_min, value=defaults.get('volume', {}).get('max_desired', context.baseline_volume * 2),
            key=f"{agent_name}_vol_max"
        )
        zopa_boundaries['volume'] = {'min_acceptable': vol_min, 'max_desired': vol_max}
        
        st.write("**Payment Terms (days)**")
        pay_min = st.number_input(
            f"Min Acceptable Payment Terms",
            min_value=0, max_value=365, value=defaults.get('payment_terms', {}).get('min_acceptable', 15),
            key=f"{agent_name}_pay_min"
        )
        pay_max = st.number_input(
            f"Max Desired Payment Terms",
            min_value=pay_min, max_value=365, value=defaults.get('payment_terms', {}).get('max_desired', 90),
            key=f"{agent_name}_pay_max"
        )
        zopa_boundaries['payment_terms'] = {'min_acceptable': pay_min, 'max_desired': pay_max}
    
    with col2:
        st.write("**Price ($/unit)**")
        # Calculate safe defaults to avoid validation errors
        default_price_min = max(0.01, defaults.get('price', {}).get('min_acceptable', context.baseline_price * 0.8))
        default_price_max = max(default_price_min + 0.01, defaults.get('price', {}).get('max_desired', context.baseline_price * 1.5))
        
        price_min = st.number_input(
            f"Min Acceptable Price",
            min_value=0.01, value=default_price_min, format="%.2f",
            key=f"{agent_name}_price_min"
        )
        price_max = st.number_input(
            f"Max Desired Price",
            min_value=max(0.02, price_min + 0.01), value=max(price_min + 0.01, default_price_max), format="%.2f",
            key=f"{agent_name}_price_max"
        )
        zopa_boundaries['price'] = {'min_acceptable': price_min, 'max_desired': price_max}
        
        st.write("**Contract Duration (months)**")
        dur_min = st.number_input(
            f"Min Acceptable Duration",
            min_value=1, max_value=120, value=defaults.get('contract_duration', {}).get('min_acceptable', 6),
            key=f"{agent_name}_dur_min"
        )
        dur_max = st.number_input(
            f"Max Desired Duration",
            min_value=dur_min, max_value=120, value=defaults.get('contract_duration', {}).get('max_desired', 36),
            key=f"{agent_name}_dur_max"
        )
        zopa_boundaries['contract_duration'] = {'min_acceptable': dur_min, 'max_desired': dur_max}
    
    return zopa_boundaries


def create_tactics_selection(agent_name: str, available_tactics: List[Dict], default_selected: Optional[List[str]] = None) -> List[str]:
    """Create tactics selection interface."""
    st.subheader(f"⚔️ {agent_name} Negotiation Tactics")
    
    default_selected = default_selected or []
    
    # Group tactics by category
    influencing_tactics = [t for t in available_tactics if t['category'] == 'Influencing']
    strategic_tactics = [t for t in available_tactics if t['category'] == 'Strategic']
    
    selected_tactics = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Influencing Techniques**")
        for tactic in influencing_tactics:
            if st.checkbox(
                f"{tactic['name']}", 
                value=tactic['id'] in default_selected,
                help=tactic['description'],
                key=f"{agent_name}_{tactic['id']}"
            ):
                selected_tactics.append(tactic['id'])
    
    with col2:
        st.write("**Strategic Tactics**")
        for tactic in strategic_tactics:
            if st.checkbox(
                f"{tactic['name']}", 
                value=tactic['id'] in default_selected,
                help=tactic['description'],
                key=f"{agent_name}_{tactic['id']}"
            ):
                selected_tactics.append(tactic['id'])
    
    return selected_tactics


def create_agent_configuration_form(agent_name: str, context: NegotiationContext, available_tactics: List[Dict]) -> Optional[AgentConfig]:
    """Create complete agent configuration form."""
    st.markdown(f'<div class="section-header">👤 {agent_name} Configuration</div>', unsafe_allow_html=True)
    
    with st.form(f"{agent_name.lower()}_config_form"):
        # Basic info
        agent_display_name = st.text_input("Agent Name", value=f"{agent_name} Agent")
        agent_description = st.text_area("Agent Description", value=f"Professional {agent_name.lower()} with negotiation experience")
        
        # Personality presets
        st.subheader("🎭 Personality Presets")
        preset = st.selectbox(
            "Choose a preset (optional)",
            options=["Custom", "Collaborative Professional", "Competitive Negotiator", "Analytical Buyer", "Relationship-Focused Seller"],
            key=f"{agent_name}_preset"
        )
        
        # Apply preset values
        preset_values = get_personality_preset(preset)
        personality = create_personality_sliders(agent_name, preset_values)
        
        # Power level
        st.subheader("💪 Power Level")
        power_level = st.slider("Negotiation Power", min_value=0.0, max_value=1.0, value=0.6, step=0.1, key=f"{agent_name}_power")
        power_description = st.text_input("Power Description", value="Market position and alternatives", key=f"{agent_name}_power_desc")
        
        # ZOPA boundaries
        zopa_boundaries = create_zopa_configuration(agent_name, context)
        
        # Tactics selection
        selected_tactics = create_tactics_selection(agent_name, available_tactics)
        
        submitted = st.form_submit_button(f"Save {agent_name} Configuration", type="primary")
        
        if submitted:
            try:
                agent_config = AgentConfig(
                    name=agent_display_name,
                    description=agent_description,
                    personality=personality,
                    power_level=PowerLevel(level=power_level, description=power_description),
                    selected_tactics=selected_tactics,
                    zopa_boundaries=zopa_boundaries
                )
                st.success(f"✅ {agent_name} configuration saved successfully!")
                return agent_config
            except Exception as e:
                st.error(f"❌ Error creating {agent_name} configuration: {str(e)}")
                return None
    
    return None


def get_personality_preset(preset_name: str) -> Dict[str, float]:
    """Get personality values for a preset."""
    presets = {
        "Collaborative Professional": {
            "openness": 0.7, "conscientiousness": 0.8, "extraversion": 0.6, 
            "agreeableness": 0.8, "neuroticism": 0.3
        },
        "Competitive Negotiator": {
            "openness": 0.5, "conscientiousness": 0.7, "extraversion": 0.8, 
            "agreeableness": 0.3, "neuroticism": 0.2
        },
        "Analytical Buyer": {
            "openness": 0.6, "conscientiousness": 0.9, "extraversion": 0.4, 
            "agreeableness": 0.5, "neuroticism": 0.3
        },
        "Relationship-Focused Seller": {
            "openness": 0.8, "conscientiousness": 0.6, "extraversion": 0.7, 
            "agreeableness": 0.9, "neuroticism": 0.2
        }
    }
    return presets.get(preset_name, {})


def analyze_zopa_overlap(agent1_config: AgentConfig, agent2_config: AgentConfig) -> Dict[str, Any]:
    """Analyze ZOPA overlap between two agents."""
    dimensions = ['volume', 'price', 'payment_terms', 'contract_duration']
    analysis = {}
    
    for dim in dimensions:
        agent1_zopa = agent1_config.zopa_boundaries.get(dim, {})
        agent2_zopa = agent2_config.zopa_boundaries.get(dim, {})
        
        if agent1_zopa and agent2_zopa:
            # Check for overlap
            overlap_min = max(agent1_zopa['min_acceptable'], agent2_zopa['min_acceptable'])
            overlap_max = min(agent1_zopa['max_desired'], agent2_zopa['max_desired'])
            
            has_overlap = overlap_min <= overlap_max
            
            analysis[dim] = {
                'has_overlap': has_overlap,
                'agent1_range': (agent1_zopa['min_acceptable'], agent1_zopa['max_desired']),
                'agent2_range': (agent2_zopa['min_acceptable'], agent2_zopa['max_desired']),
                'overlap_range': (overlap_min, overlap_max) if has_overlap else None
            }
    
    return analysis


def display_zopa_analysis(analysis: Dict[str, Any]):
    """Display ZOPA analysis with visualizations."""
    st.markdown('<div class="section-header">📊 ZOPA Analysis</div>', unsafe_allow_html=True)
    
    # Summary
    total_dimensions = len(analysis)
    overlapping_dimensions = sum(1 for dim_analysis in analysis.values() if dim_analysis['has_overlap'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Dimensions", total_dimensions)
    with col2:
        st.metric("Overlapping Dimensions", overlapping_dimensions)
    with col3:
        overlap_percentage = (overlapping_dimensions / total_dimensions) * 100 if total_dimensions > 0 else 0
        st.metric("Overlap Percentage", f"{overlap_percentage:.1f}%")
    
    # Detailed analysis
    for dim_name, dim_analysis in analysis.items():
        st.subheader(f"{dim_name.replace('_', ' ').title()}")
        
        if dim_analysis['has_overlap']:
            st.markdown(f'<div class="zopa-overlap">✅ <strong>Overlap Found</strong></div>', unsafe_allow_html=True)
            overlap_range = dim_analysis['overlap_range']
            st.write(f"**Overlap Range:** {overlap_range[0]} - {overlap_range[1]}")
        else:
            st.markdown(f'<div class="zopa-no-overlap">❌ <strong>No Overlap</strong></div>', unsafe_allow_html=True)
        
        # Show ranges
        agent1_range = dim_analysis['agent1_range']
        agent2_range = dim_analysis['agent2_range']
        st.write(f"**Agent 1 Range:** {agent1_range[0]} - {agent1_range[1]}")
        st.write(f"**Agent 2 Range:** {agent2_range[0]} - {agent2_range[1]}")


def run_negotiation_with_interface_config(
    context: NegotiationContext,
    agent1_config: AgentConfig,
    agent2_config: AgentConfig,
    max_rounds: int,
    verbose: bool,
    progress_bar,
    status_text
) -> Optional[Dict[str, Any]]:
    """Run a negotiation using the interface configuration."""
    try:
        import asyncio
        import time
        
        # Update progress
        progress_bar.progress(0.1)
        status_text.text("🏭 Creating agent factory...")
        
        # Create agent factory
        factory = AgentFactory()
        
        # Create negotiation dimensions from agent configs
        dimensions = []
        for dim_name in ['volume', 'price', 'payment_terms', 'contract_duration']:
            agent1_zopa = agent1_config.zopa_boundaries.get(dim_name, {})
            agent2_zopa = agent2_config.zopa_boundaries.get(dim_name, {})
            
            if agent1_zopa and agent2_zopa:
                dimension = NegotiationDimension(
                    name=getattr(DimensionType, dim_name.upper()),
                    unit=get_dimension_unit(dim_name),
                    agent1_min=agent1_zopa['min_acceptable'],
                    agent1_max=agent1_zopa['max_desired'],
                    agent2_min=agent2_zopa['min_acceptable'],
                    agent2_max=agent2_zopa['max_desired']
                )
                dimensions.append(dimension)
        
        progress_bar.progress(0.2)
        status_text.text("🤖 Setting up AI agents...")
        
        # Create negotiation runner
        runner = NegotiationRunner(factory)
        
        progress_bar.progress(0.3)
        status_text.text("🚀 Starting negotiation...")
        
        # Run the negotiation
        async def run_async_negotiation():
            return await runner.run_negotiation(
                agent1_config=agent1_config,
                agent2_config=agent2_config,
                dimensions=dimensions,
                max_rounds=max_rounds,
                verbose=verbose
            )
        
        # Update progress during negotiation
        for i in range(4, 9):
            progress_bar.progress(i * 0.1)
            status_text.text(f"💬 Negotiation in progress... Round {i-3}")
            time.sleep(0.5)  # Simulate progress
        
        # Run the actual negotiation
        final_state = asyncio.run(run_async_negotiation())
        
        progress_bar.progress(0.9)
        status_text.text("📊 Analyzing results...")
        
        # Get negotiation summary
        summary = runner.get_negotiation_summary()
        
        progress_bar.progress(1.0)
        status_text.text("✅ Negotiation completed!")
        
        # Format results for interface
        result = {
            'agreement_reached': final_state.status.value == 'agreement_reached',
            'total_turns': len(final_state.turns),
            'total_rounds': final_state.current_round,
            'duration_seconds': (final_state.ended_at - final_state.started_at).total_seconds() if final_state.ended_at and final_state.started_at else 0,
            'final_state': final_state,
            'summary': summary
        }
        
        # Add final agreement if reached
        if result['agreement_reached'] and final_state.result and final_state.result.final_agreement:
            result['final_agreement'] = final_state.result.final_agreement
        
        # Add failure reason if not successful
        if not result['agreement_reached']:
            result['failure_reason'] = final_state.result.failure_reason if final_state.result else "Unknown"
        
        return result
        
    except Exception as e:
        status_text.text(f"❌ Error: {str(e)}")
        st.error(f"Negotiation failed: {str(e)}")
        return None


def get_dimension_unit(dimension_name: str) -> str:
    """Get the unit for a dimension."""
    units = {
        'volume': 'units',
        'price': '$/unit',
        'payment_terms': 'days',
        'contract_duration': 'months'
    }
    return units.get(dimension_name, 'units')


def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤝 AI Negotiation Configurator</div>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Setup", "Configuration", "Analysis", "Run Negotiation", "Results"]
    )
    
    if page == "Setup":
        st.markdown("## 📋 Negotiation Setup")
        st.write("Configure the basic context and parameters for your negotiation.")
        
        # Negotiation context form
        context = create_negotiation_context_form()
        if context:
            st.session_state.negotiation_context = context
            
        # Display current context if available
        if st.session_state.negotiation_context:
            st.success("✅ Context configured successfully!")
            with st.expander("View Current Context"):
                context_dict = st.session_state.negotiation_context.to_dict()
                st.json(context_dict)
    
    elif page == "Configuration":
        if not st.session_state.negotiation_context:
            st.warning("⚠️ Please configure the negotiation context first in the Setup page.")
            return
        
        st.markdown("## 👥 Agent Configuration")
        st.write("Configure the personalities, power levels, and tactics for both negotiating agents.")
        
        # Agent configuration tabs
        tab1, tab2 = st.tabs(["Agent 1 (Buyer)", "Agent 2 (Seller)"])
        
        with tab1:
            agent1_config = create_agent_configuration_form("Buyer", st.session_state.negotiation_context, st.session_state.available_tactics)
            if agent1_config:
                st.session_state.agent1_config = agent1_config
        
        with tab2:
            agent2_config = create_agent_configuration_form("Seller", st.session_state.negotiation_context, st.session_state.available_tactics)
            if agent2_config:
                st.session_state.agent2_config = agent2_config
    
    elif page == "Analysis":
        if not all([st.session_state.negotiation_context, st.session_state.agent1_config, st.session_state.agent2_config]):
            st.warning("⚠️ Please complete the setup and configuration first.")
            return
        
        st.markdown("## 📊 Pre-Negotiation Analysis")
        
        # ZOPA Analysis
        analysis = analyze_zopa_overlap(st.session_state.agent1_config, st.session_state.agent2_config)
        display_zopa_analysis(analysis)
        
        # Agent summaries
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👤 Agent 1 Summary")
            st.write(f"**Name:** {st.session_state.agent1_config.name}")
            st.write(f"**Power Level:** {st.session_state.agent1_config.power_level.get_category()}")
            st.write(f"**Tactics:** {', '.join(st.session_state.agent1_config.selected_tactics)}")
            st.write(f"**Personality:** {st.session_state.agent1_config.personality.get_summary()}")
        
        with col2:
            st.subheader("👤 Agent 2 Summary")
            st.write(f"**Name:** {st.session_state.agent2_config.name}")
            st.write(f"**Power Level:** {st.session_state.agent2_config.power_level.get_category()}")
            st.write(f"**Tactics:** {', '.join(st.session_state.agent2_config.selected_tactics)}")
            st.write(f"**Personality:** {st.session_state.agent2_config.personality.get_summary()}")
    
    elif page == "Run Negotiation":
        if not all([st.session_state.negotiation_context, st.session_state.agent1_config, st.session_state.agent2_config]):
            st.warning("⚠️ Please complete the setup and configuration first.")
            return
        
        st.markdown("## 🚀 Run AI Negotiation")
        st.write("Execute the negotiation with your configured agents.")
        
        # Check if OpenAI API key is available
        import os
        api_key_available = bool(os.getenv('OPENAI_API_KEY'))
        
        if not api_key_available:
            st.error("❌ OpenAI API key not found! Please add your API key to the .env file.")
            st.code("OPENAI_API_KEY=your_openai_api_key_here")
            st.write("Get your API key from: https://platform.openai.com/api-keys")
            return
        
        # Negotiation parameters
        col1, col2 = st.columns(2)
        with col1:
            max_rounds = st.number_input("Maximum Rounds", min_value=1, max_value=20, value=6)
        with col2:
            verbose_output = st.checkbox("Verbose Output", value=True)
        
        if st.button("🚀 Start Negotiation", type="primary"):
            if not OPENAI_AGENTS_AVAILABLE:
                st.error("❌ OpenAI agents framework not available. Please check your installation.")
                
                # Show detailed error information
                with st.expander("🔧 Installation Instructions"):
                    st.write("**The OpenAI agents framework is required to run negotiations.**")
                    st.write("")
                    st.write("**Error Details:**")
                    st.code(f"ImportError: {IMPORT_ERROR}")
                    st.write("")
                    st.write("**To fix this issue:**")
                    st.write("1. Install the OpenAI agents framework:")
                    st.code("pip install openai-agents")
                    st.write("2. If that doesn't work, try installing from GitHub:")
                    st.code("pip install git+https://github.com/openai/openai-agents-python.git")
                    st.write("3. Restart the Streamlit application")
                    st.write("")
                    st.write("**Alternative: Use the basic negotiation engine**")
                    st.write("You can still test the system logic using the basic negotiation engine in the demo files.")
                    st.code("python demo.py")
                
                return
                
            st.info("🤖 Starting AI negotiation... This may take a few minutes.")
            
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Run the actual negotiation
                result = run_negotiation_with_interface_config(
                    st.session_state.negotiation_context,
                    st.session_state.agent1_config,
                    st.session_state.agent2_config,
                    max_rounds,
                    verbose_output,
                    progress_bar,
                    status_text
                )
                
                if result:
                    st.session_state.negotiation_results = result
                    st.success("✅ Negotiation completed successfully!")
                    st.balloons()
                    
                    # Show quick summary
                    st.subheader("Quick Results Summary")
                    if result.get('agreement_reached'):
                        st.success(f"🎉 Agreement reached in {result.get('total_turns', 0)} turns!")
                        if result.get('final_agreement'):
                            agreement = result['final_agreement']
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Volume", f"{agreement.get('volume', 0):,} units")
                            with col2:
                                st.metric("Price", f"${agreement.get('price', 0):.2f}/unit")
                            with col3:
                                st.metric("Payment", f"{agreement.get('payment_terms', 0)} days")
                            with col4:
                                st.metric("Duration", f"{agreement.get('contract_duration', 0)} months")
                    else:
                        st.warning(f"⚠️ No agreement reached. Reason: {result.get('failure_reason', 'Unknown')}")
                    
                    st.info("📊 View detailed results in the 'Results' page.")
                else:
                    st.error("❌ Negotiation failed to complete.")
                    
            except Exception as e:
                st.error(f"❌ Error during negotiation: {str(e)}")
                st.write("Please check your OpenAI API key and try again.")
    
    elif page == "Results":
        st.markdown("## 📈 Negotiation Results")
        st.write("View and analyze the results of completed negotiations.")
        
        if st.session_state.negotiation_results:
            result = st.session_state.negotiation_results
            
            # Overall status
            if result.get('agreement_reached'):
                st.success("🎉 **Agreement Successfully Reached!**")
            else:
                st.error("❌ **No Agreement Reached**")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Turns", result.get('total_turns', 0))
            with col2:
                st.metric("Total Rounds", result.get('total_rounds', 0))
            with col3:
                duration = result.get('duration_seconds', 0)
                st.metric("Duration", f"{duration:.1f}s")
            with col4:
                if result.get('agreement_reached'):
                    st.metric("Status", "✅ Success", delta="Agreement")
                else:
                    st.metric("Status", "❌ Failed", delta="No Deal")
            
            # Final agreement details
            if result.get('agreement_reached') and result.get('final_agreement'):
                st.subheader("📋 Final Agreement")
                agreement = result['final_agreement']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Volume:**", f"{agreement.get('volume', 0):,} units")
                    st.write("**Price:**", f"${agreement.get('price', 0):.2f} per unit")
                with col2:
                    st.write("**Payment Terms:**", f"{agreement.get('payment_terms', 0)} days")
                    st.write("**Contract Duration:**", f"{agreement.get('contract_duration', 0)} months")
                
                # Calculate total value
                total_value = agreement.get('volume', 0) * agreement.get('price', 0)
                st.write("**Total Contract Value:**", f"${total_value:,.2f}")
            
            # Failure reason
            elif not result.get('agreement_reached'):
                st.subheader("❌ Failure Analysis")
                failure_reason = result.get('failure_reason', 'Unknown reason')
                st.write(f"**Reason:** {failure_reason}")
            
            # Negotiation turns summary
            if result.get('final_state') and hasattr(result['final_state'], 'turns'):
                st.subheader("💬 Negotiation Exchange")
                turns = result['final_state'].turns
                
                if turns:
                    for i, turn in enumerate(turns[-5:], 1):  # Show last 5 turns
                        with st.expander(f"Turn {len(turns) - 5 + i}: {turn.agent_id}"):
                            st.write("**Message:**", turn.message)
                            if hasattr(turn, 'offer') and turn.offer:
                                st.write("**Offer:**", turn.offer)
                            if hasattr(turn, 'reasoning') and turn.reasoning:
                                st.write("**Reasoning:**", turn.reasoning)
                else:
                    st.write("No negotiation turns recorded.")
            
            # Export options
            st.subheader("📤 Export Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Export as JSON"):
                    json_data = json.dumps(result, indent=2, default=str)
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name="negotiation_results.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("📊 Export Summary"):
                    summary_text = f"""
Negotiation Results Summary

Status: {'Agreement Reached' if result.get('agreement_reached') else 'No Agreement'}
Total Turns: {result.get('total_turns', 0)}
Total Rounds: {result.get('total_rounds', 0)}
Duration: {result.get('duration_seconds', 0):.1f} seconds

"""
                    if result.get('final_agreement'):
                        agreement = result['final_agreement']
                        summary_text += f"""
Final Agreement:
- Volume: {agreement.get('volume', 0):,} units
- Price: ${agreement.get('price', 0):.2f} per unit
- Payment Terms: {agreement.get('payment_terms', 0)} days
- Contract Duration: {agreement.get('contract_duration', 0)} months
- Total Value: ${agreement.get('volume', 0) * agreement.get('price', 0):,.2f}
"""
                    
                    st.download_button(
                        label="Download Summary",
                        data=summary_text,
                        file_name="negotiation_summary.txt",
                        mime="text/plain"
                    )
            
            with col3:
                if st.button("🔄 Run New Negotiation"):
                    st.session_state.negotiation_results = None
                    st.rerun()
        else:
            st.info("ℹ️ No negotiation results available. Run a negotiation first.")
            
            # Quick start button
            if st.button("🚀 Go to Run Negotiation"):
                st.session_state.page = "Run Negotiation"
                st.rerun()


if __name__ == "__main__":
    main()
