# YAML-Based Prompt System Guide

## Overview

The ARIAN negotiation platform now uses a flexible YAML-based prompt system that allows you to easily customize how negotiation agents behave without modifying code. This guide explains how to use and customize the prompt templates.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Template Structure](#template-structure)
3. [Using Scenarios](#using-scenarios)
4. [Industry Contexts](#industry-contexts)
5. [Cultural Styles](#cultural-styles)
6. [Creating Custom Templates](#creating-custom-templates)
7. [Advanced Features](#advanced-features)
8. [Examples](#examples)

## Quick Start

### Basic Usage

```python
from agents_openai.agent_factory import AgentFactory

# Create factory and agent configuration
factory = AgentFactory()
agent_config = factory.create_buyer_agent(name="Alice")

# Create agent with default template
agent = factory.create_negotiation_agent(
    agent_config=agent_config,
    negotiation_state=negotiation_state
)
```

### Using a Scenario

```python
# Create an aggressive buyer
agent = factory.create_negotiation_agent(
    agent_config=agent_config,
    negotiation_state=negotiation_state,
    scenario="aggressive_buyer"  # Predefined scenario
)
```

## Template Structure

The main template is located at: `negotiation_poc/prompts/negotiation_prompt_template.yaml`

### Key Sections

1. **base_instruction**: The main prompt template with variables
2. **personality_templates**: Personality trait interpretations
3. **tactic_templates**: Negotiation tactic descriptions
4. **instructions**: Core behavioral guidelines
5. **scenarios**: Predefined behavior modifications
6. **industry_contexts**: Domain-specific knowledge
7. **cultural_styles**: Communication adaptations

### Variables

The template uses variables that are automatically filled:

- `{agent_name}`: Agent's name
- `{agent_description}`: Agent's role description
- `{personality_section}`: Generated personality traits
- `{power_category}`: Power level category
- `{power_sources}`: Sources of negotiation power
- `{tactics_section}`: Selected tactics
- `{zopa_section}`: ZOPA boundaries
- `{negotiation_status}`: Current negotiation state
- `{instructions_list}`: Behavioral instructions
- `{response_format}`: Output format specification

## Using Scenarios

Scenarios modify agent behavior for specific situations:

### Available Scenarios

1. **aggressive_buyer**: Push hard for better terms
2. **relationship_focused**: Emphasize long-term partnership
3. **crisis_negotiation**: Handle urgent situations
4. **premium_positioning**: Maintain premium value

### Example

```python
# Relationship-focused seller
agent = factory.create_negotiation_agent(
    agent_config=seller_config,
    negotiation_state=negotiation_state,
    scenario="relationship_focused"
)
```

### Scenario Effects

- Modifies personality traits (e.g., increases agreeableness)
- Adds specific instructions
- Changes negotiation approach

## Industry Contexts

Add domain-specific knowledge to agents:

### Available Industries

1. **technology**: Software, IT, tech products
2. **manufacturing**: Physical goods, supply chain
3. **retail**: Consumer products, inventory
4. **services**: Professional services, consulting

### Example

```python
# Technology industry seller
agent = factory.create_negotiation_agent(
    agent_config=seller_config,
    negotiation_state=negotiation_state,
    industry="technology"
)
```

## Cultural Styles

Adapt communication patterns:

### Available Styles

1. **direct**: Explicit, fact-based communication
2. **indirect**: Context-heavy, relationship-first
3. **formal**: Hierarchical, protocol-focused

### Example

```python
# Indirect communication style
agent = factory.create_negotiation_agent(
    agent_config=agent_config,
    negotiation_state=negotiation_state,
    cultural_style="indirect"
)
```

## Creating Custom Templates

### Step 1: Create YAML File

```yaml
negotiation_agent_prompt:
  base_instruction: |
    You are {agent_name}, a specialized negotiator.
    
    CUSTOM RULES:
    - Always seek win-win outcomes
    - Focus on value creation
    
    {personality_section}
    {tactics_section}
    {zopa_section}
    {negotiation_status}
    {instructions_list}
    {response_format}
  
  personality_templates:
    high_openness: "- Embrace innovative solutions"
    # ... other traits
  
  instructions:
    default:
      - "Follow custom guidelines"
      - "Be creative"
```

### Step 2: Use Custom Template

```python
agent = factory.create_negotiation_agent(
    agent_config=agent_config,
    negotiation_state=negotiation_state,
    template_path="path/to/custom_template.yaml"
)
```

## Advanced Features

### Combining Multiple Features

```python
# Aggressive buyer in technology with formal style
agent = factory.create_negotiation_agent(
    agent_config=buyer_config,
    negotiation_state=negotiation_state,
    scenario="aggressive_buyer",
    industry="technology",
    cultural_style="formal"
)
```

### Dynamic Prompt Reloading

```python
# Reload template after modifications
agent.prompt_manager.reload_template()
```

### Getting Available Options

```python
from utils.prompt_template_manager import PromptTemplateManager

manager = PromptTemplateManager()
print("Scenarios:", manager.get_available_scenarios())
print("Industries:", manager.get_available_industries())
print("Cultural Styles:", manager.get_available_cultural_styles())
```

## Examples

### Example 1: Cost-Focused Buyer

```python
# Create aggressive buyer for manufacturing
buyer_config = factory.create_buyer_agent(
    name="Cost Cutter",
    personality_traits={
        "agreeableness": 0.3,  # Low cooperation
        "extraversion": 0.8,   # Assertive
        "neuroticism": 0.2     # Confident
    }
)

agent = factory.create_negotiation_agent(
    agent_config=buyer_config,
    negotiation_state=negotiation_state,
    scenario="aggressive_buyer",
    industry="manufacturing"
)
```

### Example 2: Relationship Builder

```python
# Create relationship-focused seller
seller_config = factory.create_seller_agent(
    name="Partnership Builder",
    personality_traits={
        "agreeableness": 0.8,  # High cooperation
        "openness": 0.7,       # Creative solutions
        "extraversion": 0.7    # Engaging
    }
)

agent = factory.create_negotiation_agent(
    agent_config=seller_config,
    negotiation_state=negotiation_state,
    scenario="relationship_focused",
    industry="services",
    cultural_style="indirect"
)
```

### Example 3: Custom Template for Specific Product

Create `premium_chocolate_template.yaml`:

```yaml
negotiation_agent_prompt:
  base_instruction: |
    You are {agent_name}, a premium chocolate specialist.
    
    PRODUCT FOCUS: Premium Swiss Chocolate
    - Emphasize quality and craftsmanship
    - Highlight sustainable sourcing
    - Focus on luxury positioning
    
    {personality_section}
    {tactics_section}
    {zopa_section}
    {negotiation_status}
    {instructions_list}
    {response_format}
```

Use it:

```python
agent = factory.create_negotiation_agent(
    agent_config=seller_config,
    negotiation_state=negotiation_state,
    template_path="premium_chocolate_template.yaml"
)
```

## Best Practices

1. **Start with Scenarios**: Use predefined scenarios before creating custom templates
2. **Test Incrementally**: Make small changes and test their effects
3. **Document Changes**: Keep notes on what modifications work best
4. **Version Control**: Track template changes in Git
5. **Validate Output**: Always test that agents still produce valid offers

## Troubleshooting

### Common Issues

1. **Template Not Found**
   - Check file path is correct
   - Ensure YAML file exists

2. **Invalid YAML**
   - Validate YAML syntax
   - Check indentation (use spaces, not tabs)

3. **Missing Variables**
   - Ensure all required sections exist
   - Check variable names match exactly

### Debug Mode

```python
# Print generated prompt for debugging
prompt = agent._generate_instructions()
print(prompt)
```

## Summary

The YAML-based prompt system provides:

- **Flexibility**: Modify behavior without code changes
- **Reusability**: Share templates across projects
- **Clarity**: Prompts are readable and maintainable
- **Power**: Combine multiple modifications easily

Start with the default template and scenarios, then create custom templates as needed for your specific use cases.
