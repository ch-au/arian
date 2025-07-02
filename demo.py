#!/usr/bin/env python3
"""
OpenAI Agents Negotiation Demo

This script demonstrates a real negotiation between two OpenAI agents
using our personality, tactics, and ZOPA configurations.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models.negotiation import NegotiationDimension, DimensionType
from agents_openai.agent_factory import AgentFactory
from agents_openai.negotiation_runner import NegotiationRunner


def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Environment variables loaded from .env file")
    else:
        print("⚠️  No .env file found. Please create one based on .env.example")
        print("   You can copy .env.example to .env and add your OpenAI API key")
        return False
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please add your OpenAI API key to the .env file")
        return False
    
    print("✅ OpenAI API key found")
    return True


def create_negotiation_dimensions():
    """Create the negotiation dimensions with ZOPA analysis."""
    return [
        NegotiationDimension(
            name=DimensionType.VOLUME,
            unit="units",
            agent1_min=1000,  # Buyer minimum
            agent1_max=5000,  # Buyer maximum
            agent2_min=2000,  # Seller minimum
            agent2_max=8000   # Seller maximum
        ),
        NegotiationDimension(
            name=DimensionType.PRICE,
            unit="$/unit",
            agent1_min=8.0,   # Buyer minimum
            agent1_max=15.0,  # Buyer maximum
            agent2_min=12.0,  # Seller minimum
            agent2_max=20.0   # Seller maximum
        ),
        NegotiationDimension(
            name=DimensionType.PAYMENT_TERMS,
            unit="days",
            agent1_min=30,    # Buyer minimum
            agent1_max=90,    # Buyer maximum
            agent2_min=15,    # Seller minimum
            agent2_max=60     # Seller maximum
        ),
        NegotiationDimension(
            name=DimensionType.CONTRACT_DURATION,
            unit="months",
            agent1_min=6,     # Buyer minimum
            agent1_max=24,    # Buyer maximum
            agent2_min=12,    # Seller minimum
            agent2_max=36     # Seller maximum
        )
    ]


async def run_openai_negotiation():
    """Run a complete negotiation using OpenAI agents."""
    print("🤖 Starting OpenAI Agents Negotiation Demo")
    print("="*60)
    
    # Load environment
    if not load_environment():
        return False
    
    # Create agent factory
    print("\n🏭 Creating agent factory...")
    factory = AgentFactory()
    
    # Create buyer agent with specific personality
    print("\n👤 Creating buyer agent...")
    buyer_config = factory.create_buyer_agent(
        name="Alice (Procurement Manager)",
        description="Experienced procurement manager focused on cost optimization and supplier relationships",
        personality_traits={
            "openness": 0.6,          # Moderately open to new ideas
            "conscientiousness": 0.8, # Very detail-oriented and systematic
            "extraversion": 0.5,      # Balanced communication style
            "agreeableness": 0.7,     # Cooperative but firm on requirements
            "neuroticism": 0.3        # Calm under pressure
        },
        power_level=0.6,
        power_sources=["Budget Authority", "Multiple Supplier Options", "Market Research"],
        selected_tactics=["collaborative", "anchoring"]
    )
    
    # Create seller agent with different personality
    print("👤 Creating seller agent...")
    seller_config = factory.create_seller_agent(
        name="Bob (Sales Director)",
        description="Senior sales director with strong relationship-building skills and market expertise",
        personality_traits={
            "openness": 0.7,          # Creative in finding solutions
            "conscientiousness": 0.6, # Organized but flexible
            "extraversion": 0.8,      # Confident and assertive
            "agreeableness": 0.5,     # Balanced cooperation and competition
            "neuroticism": 0.2        # Very calm and confident
        },
        power_level=0.7,
        power_sources=["Product Expertise", "Pricing Flexibility", "Strong Market Position"],
        selected_tactics=["rapport_building", "competitive"]
    )
    
    print(f"✅ Buyer: {buyer_config.name}")
    print(f"   Personality: {buyer_config.personality.get_summary()}")
    print(f"   Power: {buyer_config.power_level.get_category()}")
    print(f"   Tactics: {', '.join(buyer_config.selected_tactics)}")
    
    print(f"✅ Seller: {seller_config.name}")
    print(f"   Personality: {seller_config.personality.get_summary()}")
    print(f"   Power: {seller_config.power_level.get_category()}")
    print(f"   Tactics: {', '.join(seller_config.selected_tactics)}")
    
    # Create negotiation dimensions
    print("\n📊 Setting up negotiation dimensions...")
    dimensions = create_negotiation_dimensions()
    
    # Create negotiation runner
    print("\n🎬 Initializing negotiation runner...")
    runner = NegotiationRunner(factory)
    
    # Run the negotiation
    print("\n🚀 Starting AI-to-AI negotiation...")
    print("   This may take a few minutes as the agents think and respond...")
    
    try:
        final_state = await runner.run_negotiation(
            agent1_config=buyer_config,
            agent2_config=seller_config,
            dimensions=dimensions,
            max_rounds=6,  # Reasonable number for demo
            verbose=True
        )
        
        # Print summary
        summary = runner.get_negotiation_summary()
        if summary:
            print("\n📋 NEGOTIATION SUMMARY:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during negotiation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_quick_test():
    """Run a quick test to verify OpenAI agents integration works."""
    print("🧪 Running Quick OpenAI Agents Test")
    print("="*50)
    
    # Load environment
    if not load_environment():
        return False
    
    try:
        # Test basic agent creation
        print("\n🔧 Testing agent creation...")
        factory = AgentFactory()
        
        buyer_config = factory.create_buyer_agent(name="Test Buyer")
        seller_config = factory.create_seller_agent(name="Test Seller")
        
        print("✅ Agent configurations created successfully")
        
        # Test negotiation setup (without running full negotiation)
        print("\n🔧 Testing negotiation setup...")
        dimensions = create_negotiation_dimensions()
        runner = NegotiationRunner(factory)
        
        print("✅ Negotiation runner initialized successfully")
        print("\n🎉 Quick test completed! OpenAI agents integration is ready.")
        print("\nTo run a full negotiation, use: python demo_openai_agents.py --full")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Agents Negotiation Demo")
    parser.add_argument("--full", action="store_true", help="Run full negotiation (requires OpenAI API)")
    parser.add_argument("--test", action="store_true", help="Run quick test only")
    
    args = parser.parse_args()
    
    try:
        if args.test or (not args.full and not args.test):
            # Default to quick test
            success = asyncio.run(run_quick_test())
        else:
            # Run full negotiation
            success = asyncio.run(run_openai_negotiation())
        
        if success:
            print("\n✨ Demo completed successfully!")
        else:
            print("\n❌ Demo failed. Please check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
