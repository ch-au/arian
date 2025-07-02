# OpenAI Agents Integration - Complete Implementation

This document describes the complete OpenAI Agents integration for the Negotiation POC.

## 🎯 **What We've Built**

### **Complete AI-to-AI Negotiation System**
- ✅ **Real OpenAI Agents**: Full integration with OpenAI's agents framework
- ✅ **Personality-Driven Negotiations**: Big 5 personality traits automatically generate negotiation instructions
- ✅ **Tactic-Based Communication**: Selected tactics influence agent communication style and strategy
- ✅ **ZOPA-Aware Agents**: Agents understand and respect their negotiation boundaries
- ✅ **Structured Outputs**: Agents return properly formatted offers with reasoning
- ✅ **Real-time Analysis**: Live ZOPA compliance checking and turn analysis

## 🏗️ **Architecture Overview**

```
negotiation_poc/
├── agents/                    # 🆕 OpenAI Agents Integration
│   ├── __init__.py           # Module exports
│   ├── negotiation_agent.py  # Core OpenAI agent wrapper
│   ├── agent_factory.py      # Agent creation and configuration
│   └── negotiation_runner.py # Orchestrates full negotiations
├── models/                   # Core data models
├── engine/                   # Negotiation logic
├── utils/                    # Utilities
└── demo_openai_agents.py     # 🆕 Live AI negotiation demo
```

## 🤖 **Key Components**

### **1. NegotiationAgent (`agents/negotiation_agent.py`)**
- Wraps OpenAI Agent with our custom configuration
- Generates personality-based instructions automatically
- Includes negotiation tools (ZOPA analysis, history, calculations)
- Returns structured offers with reasoning

### **2. AgentFactory (`agents/agent_factory.py`)**
- Creates buyer/seller agents with sensible defaults
- Supports custom agent configurations
- Validates agent configurations
- Provides pre-configured personality profiles

### **3. NegotiationRunner (`agents/negotiation_runner.py`)**
- Orchestrates complete AI-to-AI negotiations
- Manages turn-based flow between agents
- Provides real-time ZOPA compliance checking
- Generates detailed negotiation analytics

## 🚀 **How to Use**

### **Quick Test (No API Key Required)**
```bash
cd negotiation_poc
python demo_openai_agents.py --test
```

### **Full AI Negotiation (Requires OpenAI API Key)**
```bash
# 1. Add your OpenAI API key to .env file
echo "OPENAI_API_KEY=your_key_here" >> .env

# 2. Run full AI-to-AI negotiation
python demo_openai_agents.py --full
```

### **Integration Test**
```bash
python test_openai_agents.py
```

## 📊 **Sample Negotiation Flow**

```
🚀 Starting negotiation between Alice (Procurement Manager) and Bob (Sales Director)
📊 Max rounds: 6
📏 Dimensions: ['volume', 'price', 'payment_terms', 'contract_duration']

============================================================
ZOPA ANALYSIS
============================================================

VOLUME:
  Agent 1 range: 1000 - 5000 units
  Agent 2 range: 2000 - 8000 units
  ✅ OVERLAP: 2000 - 5000 units

PRICE:
  Agent 1 range: 8.0 - 15.0 $/unit
  Agent 2 range: 12.0 - 20.0 $/unit
  ✅ OVERLAP: 12.0 - 15.0 $/unit

--- Round 1, Turn 1 ---
🎯 Alice (Procurement Manager)'s turn
💼 Offer: 3000 units @ $13.50/unit
📅 Terms: 60 days payment, 18 months
💰 Total Value: $40,500.00
🎯 Confidence: 75%
💬 Message: "I'd like to start with a collaborative approach..."
🧠 Reasoning: Opening with mid-range offer to anchor expectations...
✅ ZOPA compliant: volume, price, payment_terms, contract_duration

--- Round 1, Turn 2 ---
🎯 Bob (Sales Director)'s turn
💼 Offer: 3500 units @ $14.25/unit
📅 Terms: 45 days payment, 24 months
💰 Total Value: $49,875.00
🎯 Confidence: 80%
💬 Message: "Great to work with you Alice. I can offer..."
🧠 Reasoning: Building rapport while positioning competitively...
✅ ZOPA compliant: volume, price, payment_terms, contract_duration

🏁 Negotiation terminating: agreement_reached

============================================================
FINAL NEGOTIATION RESULTS
============================================================
Status: agreement_reached
🎉 AGREEMENT REACHED!
📦 Volume: 3500 units
💰 Price: $14.25/unit
📅 Payment: 45 days
⏰ Duration: 24 months
💵 Total Value: $49,875.00
📊 Success Score: 85%
```

## 🎛️ **Agent Configuration**

### **Personality-Driven Instructions**
```python
# High conscientiousness buyer
personality = PersonalityProfile(
    openness=0.6,          # Moderately open to new ideas
    conscientiousness=0.8, # Very detail-oriented
    extraversion=0.5,      # Balanced communication
    agreeableness=0.7,     # Cooperative but firm
    neuroticism=0.3        # Calm under pressure
)

# Generates instructions like:
# "- Be detail-oriented and systematic in your approach"
# "- Emphasize collaboration and mutual benefits"
# "- Be calm and confident under pressure"
```

### **Tactic Integration**
```python
selected_tactics = ["collaborative", "anchoring"]

# Generates instructions like:
# "- Use collaborative language and seek mutual benefits"
# "- Make strong opening offers to anchor expectations"
```

### **ZOPA Boundaries**
```python
zopa_boundaries = {
    "volume": {"min_acceptable": 1000, "max_desired": 5000},
    "price": {"min_acceptable": 8.0, "max_desired": 15.0},
    "payment_terms": {"min_acceptable": 30, "max_desired": 90},
    "contract_duration": {"min_acceptable": 6, "max_desired": 24}
}

# Generates instructions like:
# "ZOPA BOUNDARIES (Your acceptable ranges):"
# "- Volume: 1000 to 5000"
# "- Price: 8.0 to 15.0"
```

## 🔧 **Technical Implementation**

### **OpenAI Agent Creation**
```python
from agents import Agent, function_tool

agent = Agent(
    name=self.agent_config.name,
    instructions=self._generate_instructions(),
    output_type=NegotiationOfferOutput,
    tools=[self._create_negotiation_tools()]
)
```

### **Structured Output**
```python
class NegotiationOfferOutput(BaseModel):
    volume: int
    price: float
    payment_terms: int
    contract_duration: int
    message: str
    confidence: float
    reasoning: str
```

### **Negotiation Tools**
```python
@function_tool
def analyze_zopa_overlap(dimension: str) -> str:
    """Analyze ZOPA overlap for a specific dimension."""
    # Implementation...

@function_tool
def get_negotiation_history() -> str:
    """Get a summary of the negotiation history."""
    # Implementation...
```

## 🧪 **Testing**

### **Automated Tests**
- ✅ Agent factory functionality
- ✅ Agent configuration validation
- ✅ ZOPA analysis
- ✅ Negotiation setup
- ✅ Instruction generation

### **Integration Tests**
- ✅ OpenAI agents import (graceful fallback)
- ✅ End-to-end negotiation flow
- ✅ Error handling

## 🎯 **Key Features**

### **1. Personality-Driven Behavior**
- Agents automatically adapt communication style based on Big 5 traits
- High agreeableness → collaborative language
- High extraversion → confident, assertive communication
- Low neuroticism → calm under pressure

### **2. Tactic-Based Strategy**
- Selected tactics influence negotiation approach
- "Anchoring" → strong opening offers
- "Rapport building" → relationship-focused communication
- "Competitive" → emphasize strong position

### **3. ZOPA Compliance**
- Real-time validation of offers against boundaries
- Agents understand their acceptable ranges
- Automatic detection of ZOPA violations

### **4. Structured Reasoning**
- Every offer includes detailed reasoning
- Confidence levels for each offer
- Clear communication messages

## 🚀 **Ready for Production**

The OpenAI Agents integration is complete and ready for:

1. **Real Negotiations**: Add OpenAI API key and run live negotiations
2. **Custom Scenarios**: Configure different personality types and tactics
3. **Analytics**: Built-in success scoring and negotiation analysis
4. **Extension**: Easy to add new tactics, dimensions, or agent types

## 📈 **Next Steps**

1. **Advanced Tactics**: Implement more sophisticated negotiation strategies
2. **Multi-party**: Extend to 3+ party negotiations
3. **Learning**: Add reinforcement learning for tactic optimization
4. **UI/Dashboard**: Create web interface for configuration and monitoring
5. **Analytics**: Enhanced reporting and visualization

The foundation is solid and extensible for building a full-scale AI negotiation platform!
