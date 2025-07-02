# Negotiation Simulation App - Architectural Decisions Record (ADR)

## Project Overview
**Goal:** Build a POC for a two-party negotiation simulation using OpenAI Agents, where agents negotiate across 4 dimensions (volume, price, payment conditions, contract time) with configurable personalities, tactics, and ZOPA boundaries.

## Key Architectural Decisions

### ADR-001: Technology Stack Selection
**Decision:** Use Python with OpenAI Agents SDK, Streamlit for UI, and Pydantic for data models.

**Rationale:**
- OpenAI Agents SDK provides robust multi-agent framework with built-in tracing
- Streamlit enables rapid prototyping of interactive UIs
- Pydantic ensures type safety and data validation
- Python ecosystem has excellent AI/ML libraries

**Alternatives Considered:**
- FastAPI + React frontend (more complex, longer development time)
- LangChain (less specialized for agent workflows)

**Status:** Accepted

---

### ADR-002: Agent Communication Pattern
**Decision:** Turn-based negotiation with structured outputs.

**Rationale:**
- Simpler to implement and debug than real-time
- Allows for clear state management
- Structured outputs ensure consistent offer format
- Easier to implement ZOPA validation

**Implementation:**
- Each agent produces structured JSON offers
- Turn orchestrator manages alternating exchanges
- Maximum rounds limit prevents infinite loops

**Status:** Accepted

---

### ADR-003: ZOPA Configuration Model
**Decision:** Simple min/max ranges for each negotiation dimension.

**Rationale:**
- Easy to understand and configure
- Sufficient for POC validation
- Clear overlap detection logic
- Extensible to more complex preference structures

**Data Structure:**
```python
class NegotiationDimension:
    name: str
    min_acceptable: float
    max_desired: float
    unit: str
    current_offer: Optional[float]
```

**Status:** Accepted

---

### ADR-004: Personality Integration Approach
**Decision:** Big 5 personality traits influence prompt engineering and response tone.

**Rationale:**
- Research-backed personality model
- Clear mapping to negotiation behaviors
- Configurable via 0-1 sliders
- Affects both strategy and communication style

**Implementation:**
- High agreeableness → collaborative language, more concessions
- High conscientiousness → detailed offers, systematic approach
- High extraversion → assertive communication
- High neuroticism → risk-averse behavior
- High openness → creative solutions

**Status:** Accepted

---

### ADR-005: Tactics Integration Strategy
**Decision:** Manual tactic selection with CSV import, tactics influence prompt instructions.

**Rationale:**
- Allows precise control over agent behavior
- CSV import enables easy tactic library management
- Manual selection suitable for POC scope
- Clear separation between tactics and personality

**Implementation:**
```python
class NegotiationTactic:
    name: str
    aspect: str  # Focus/Approach/Timing/Tone/Risk
    description: str
    prompt_modifier: str
    effectiveness_weight: float
```

**Status:** Accepted

---

### ADR-006: Data Persistence Strategy
**Decision:** JSON files for configuration and negotiation state persistence.

**Rationale:**
- Simple file-based storage suitable for POC
- Human-readable format for debugging
- No database setup required
- Easy backup and version control

**File Structure:**
- `agents/agent_configs.json` - Agent configurations
- `negotiations/session_{id}.json` - Negotiation sessions
- `tactics/tactics_library.json` - Imported tactics

**Status:** Accepted

---

### ADR-007: UI Framework Choice
**Decision:** Streamlit for rapid prototyping with potential FastAPI migration path.

**Rationale:**
- Fastest development for interactive prototypes
- Built-in widgets for sliders, selectors
- Real-time updates for negotiation visualization
- Easy deployment and sharing

**Components:**
- Agent configuration page
- Negotiation execution view
- ZOPA analysis dashboard
- Results export functionality

**Status:** Accepted

---

### ADR-008: Error Handling Strategy
**Decision:** Graceful degradation with comprehensive logging and user feedback.

**Rationale:**
- LLM responses can be unpredictable
- Network issues with OpenAI API
- Invalid user configurations need clear feedback

**Implementation:**
- Try/catch blocks around all LLM calls
- Validation at data model level
- User-friendly error messages in UI
- Detailed logging for debugging

**Status:** Accepted

---

### ADR-009: Testing Strategy
**Decision:** Unit tests for models and engine, integration tests for agent interactions.

**Rationale:**
- Core business logic needs reliable testing
- Agent behavior testing requires integration approach
- Mock OpenAI responses for deterministic tests

**Test Coverage:**
- Data models validation
- ZOPA calculation logic
- Turn orchestration
- Agreement detection
- Agent response parsing

**Status:** Accepted

---

### ADR-010: Extensibility Design
**Decision:** Modular architecture with clear interfaces for future enhancements.

**Rationale:**
- POC should demonstrate scalability potential
- Plugin-style architecture for new dimensions
- Interface-based design for different LLM providers

**Extension Points:**
- New negotiation dimensions
- Additional personality models
- Different LLM backends
- Multi-party negotiations
- Dynamic tactic selection

**Status:** Accepted

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [x] Project structure setup
- [x] Core data models (Pydantic)
- [x] CSV tactics import
- [x] Basic validation logic
- [x] Unit tests for models

### Phase 2: Engine (Week 2)
- [x] Negotiation orchestrator
- [x] Turn management system
- [x] ZOPA validation logic
- [x] Agreement detection
- [x] State persistence
- [x] Comprehensive test suite

### Phase 3: Agents (Week 3)
- [ ] OpenAI Agents integration
- [ ] Personality-driven prompts
- [ ] Structured output parsing
- [ ] Tactic application logic
- [ ] Agent response validation

### Phase 4: UI (Week 4)
- [ ] Streamlit application setup
- [ ] Agent configuration interface
- [ ] Live negotiation visualization
- [ ] ZOPA analysis charts
- [ ] Export/import functionality

## Success Criteria

### Functional Requirements
- [x] Two agents can negotiate across 4 dimensions
- [ ] Personality traits influence negotiation behavior
- [ ] ZOPA boundaries are respected
- [ ] Negotiations terminate appropriately
- [ ] Results are clearly visualized

### Technical Requirements
- [ ] Response time < 2 seconds per turn
- [ ] Graceful error handling
- [ ] Data persistence works reliably
- [ ] UI is intuitive and responsive
- [ ] Code is well-tested and documented

### Business Requirements
- [ ] Demonstrates clear value proposition
- [ ] Shows personality impact on outcomes
- [ ] Provides actionable insights
- [ ] Extensible for future features
- [ ] Easy to configure and use

## Risk Mitigation

### Technical Risks
- **LLM Response Variability:** Use structured outputs and validation
- **API Rate Limits:** Implement retry logic and user feedback
- **Complex State Management:** Use immutable state patterns

### Business Risks
- **Unclear Value Proposition:** Focus on clear metrics and visualizations
- **User Adoption:** Prioritize intuitive UI and clear documentation

## Future Enhancements

### Short Term (Next 3 months)
- Dynamic tactic selection based on negotiation context
- Multi-dimensional preference curves instead of simple min/max
- Integration with external market data
- Advanced personality models (Dark Triad, etc.)

### Long Term (6+ months)
- Multi-party negotiations (3+ agents)
- Real-time negotiation mode
- Machine learning for tactic effectiveness
- Integration with CRM systems
- Mobile application

---

**Document Status:** Living document, updated throughout implementation
**Last Updated:** January 7, 2025
**Next Review:** Weekly during implementation phases
