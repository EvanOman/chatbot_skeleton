# Architecture Decision Records (ADR)

## ADR-001: Domain-Driven Design Architecture

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented a domain-driven design (DDD) architecture with clean architecture principles for the chat application.

**Context:**
Need to create a maintainable, scalable chat application with clear separation of concerns and testability.

**Consequences:**
- **Positive:** Clear separation between domain logic, application services, infrastructure, and presentation layers
- **Positive:** Easy to test business logic in isolation
- **Positive:** Framework-independent core business logic
- **Negative:** Initial complexity higher than simple layered architecture

## ADR-002: Dependency Injection with dependency-injector

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Used dependency-injector library for dependency injection instead of manual dependency wiring.

**Context:**
Need to manage dependencies between layers cleanly and support different configurations (testing, production).

**Consequences:**
- **Positive:** Loose coupling between components
- **Positive:** Easy to swap implementations for testing
- **Positive:** Centralized dependency configuration
- **Negative:** Additional library dependency

## ADR-003: SQLAlchemy with AsyncPG for Database Layer

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Used SQLAlchemy 2.0 with AsyncPG driver for PostgreSQL database operations.

**Context:**
Need async database operations for FastAPI application with good ORM support.

**Consequences:**
- **Positive:** Full async support
- **Positive:** Mature ORM with good PostgreSQL support
- **Positive:** Type safety with modern SQLAlchemy 2.0 patterns
- **Negative:** Learning curve for SQLAlchemy 2.0 async patterns

## ADR-004: Repository Pattern Implementation

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented repository pattern with abstract base classes in domain layer and concrete implementations in infrastructure layer.

**Context:**
Need to abstract database operations and support potential future database changes.

**Consequences:**
- **Positive:** Database-agnostic domain layer
- **Positive:** Easy to mock for testing
- **Positive:** Clear data access patterns
- **Negative:** Additional abstraction layer

## ADR-005: EchoBot as Initial Bot Implementation

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented simple EchoBot that returns "Echo: {user_message}" as the initial bot response logic.

**Context:**
Need a simple bot implementation to demonstrate the chat functionality without external dependencies.

**Consequences:**
- **Positive:** Simple, predictable behavior for testing
- **Positive:** No external API dependencies
- **Positive:** Easy to replace with more sophisticated bot logic
- **Negative:** Limited conversational capabilities

## ADR-006: Embedded HTML Frontend

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Embedded HTML/CSS/JavaScript frontend directly in FastAPI endpoint instead of separate frontend framework.

**Context:**
Need simple frontend for demonstration without additional build complexity.

**Consequences:**
- **Positive:** Single deployment unit
- **Positive:** No build pipeline needed
- **Positive:** Direct WebSocket integration
- **Negative:** Limited scalability for complex UI
- **Negative:** Mixed concerns in backend code

## ADR-007: DSPy REACT Agent Implementation

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Replaced simple EchoBot with sophisticated DSPy REACT agent featuring chain-of-thought reasoning and tool integration.

**Context:**
User requested advanced AI capabilities with sophisticated reasoning, tool usage, and memory persistence.

**Consequences:**
- **Positive:** Advanced conversational AI with reasoning capabilities
- **Positive:** Extensible tool ecosystem (calculator, web search, weather, etc.)
- **Positive:** Chain-of-thought transparency for debugging
- **Negative:** Increased complexity and external API dependencies
- **Negative:** Higher computational and API costs

## ADR-008: BM25 Memory System

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented BM25-based information retrieval system for conversation memory and context management.

**Context:**
Need efficient text-based memory retrieval to maintain conversation context and enable agent to reference previous interactions.

**Consequences:**
- **Positive:** Fast, relevant memory retrieval based on content similarity
- **Positive:** No external dependencies for core functionality
- **Positive:** Proven algorithm for text search applications
- **Negative:** Limited to keyword-based matching (no semantic understanding)
- **Negative:** Memory grows linearly with conversation length

## ADR-009: Streaming WebSocket Responses

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented real-time streaming responses via WebSocket for improved user experience during AI agent processing.

**Context:**
AI agent responses can take several seconds to generate; users need immediate feedback and real-time response streaming.

**Consequences:**
- **Positive:** Improved user experience with real-time feedback
- **Positive:** Visual indication of processing progress
- **Positive:** Better handling of long-running AI operations
- **Negative:** Increased complexity in frontend WebSocket handling
- **Negative:** Requires careful state management for connection handling

## ADR-010: Comprehensive CLI with Typer and Rich

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Built extensive command-line interface using Typer framework with Rich formatting for developer productivity.

**Context:**
Need powerful development and management tools for database operations, testing, monitoring, and system administration.

**Consequences:**
- **Positive:** Rich developer experience with colorized output
- **Positive:** 15+ commands for comprehensive system management
- **Positive:** Type-safe command definitions with automatic help generation
- **Negative:** Additional dependencies for CLI functionality
- **Negative:** Maintenance overhead for extensive command set

## ADR-011: Performance Profiling Integration

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Integrated py-spy profiler with flame graph generation for performance analysis and optimization.

**Context:**
Need visibility into application performance bottlenecks and optimization opportunities for production readiness.

**Consequences:**
- **Positive:** Interactive flame graphs for performance analysis
- **Positive:** Multiple profiling formats (flamegraph, speedscope, memory)
- **Positive:** Both CLI and code integration options
- **Negative:** Additional system dependencies (py-spy requires system access)
- **Negative:** Profiling overhead during analysis periods

## ADR-012: Multi-format Export System

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented comprehensive export functionality supporting JSON, CSV, Markdown, and HTML formats for conversation data.

**Context:**
Users need ability to extract and share conversation data in various formats for analysis, reporting, and integration.

**Consequences:**
- **Positive:** Flexible data export for different use cases
- **Positive:** Standardized format templates with metadata inclusion
- **Positive:** HTTP streaming for large datasets
- **Negative:** Format-specific maintenance and testing requirements
- **Negative:** Potential performance impact for large conversation exports

## ADR-013: Webhook System for External Integrations

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Built webhook system with HMAC signature validation and retry logic for external service integrations.

**Context:**
Enable integration with external systems by sending real-time notifications of chat events and system activities.

**Consequences:**
- **Positive:** Secure webhook delivery with signature validation
- **Positive:** Configurable retry logic and event filtering
- **Positive:** Support for multiple webhook endpoints
- **Negative:** Additional complexity in event handling and delivery
- **Negative:** Potential security risks if webhook endpoints are compromised

## ADR-014: D3.js Conversation Tree Visualization

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented interactive conversation tree visualization using D3.js for visual analysis of chat flows.

**Context:**
Need visual representation of conversation structure and flow for analysis, debugging, and user experience enhancement.

**Consequences:**
- **Positive:** Interactive visual representation of conversation structure
- **Positive:** Helpful for debugging conversation flows and agent behavior
- **Positive:** Professional visualization using industry-standard library
- **Negative:** Additional frontend complexity with D3.js integration
- **Negative:** Performance considerations for large conversation trees

## ADR-015: AsyncPG Session-Scoped Event Loop for Testing

**Date:** 2025-07-23

**Status:** Accepted

**Decision:**
Implemented session-scoped event loop fixture and NullPool connection pooling to resolve asyncpg "cannot perform operation: another operation is in progress" errors in pytest-asyncio testing.

**Context:**
The application uses asyncpg with SQLAlchemy async sessions, but pytest-asyncio creates new event loops for each test function by default, causing connection pool conflicts and "another operation is in progress" errors, especially in CI environments like GitHub Actions.

**Solution Components:**
1. **Session-scoped event loop fixture**: All tests in a session share the same event loop
2. **NullPool for testing**: Disables connection pooling to prevent connection sharing conflicts
3. **Proper transaction isolation**: Each test gets a rollback-isolated session
4. **Enhanced connection configuration**: Added timeouts and connection metadata for CI reliability
5. **pytest-asyncio configuration**: Set `asyncio_default_fixture_loop_scope = session`

**Consequences:**
- **Positive:** Eliminates "another operation is in progress" errors in tests
- **Positive:** Reliable test execution in CI environments (GitHub Actions)
- **Positive:** Proper test isolation with transaction rollbacks
- **Positive:** Better connection management with timeouts for CI
- **Positive:** Session-scoped fixtures reduce overhead of engine creation
- **Negative:** NullPool disables connection pooling benefits during testing
- **Negative:** Session-scoped event loop means all async fixtures share the same loop
- **Negative:** Additional complexity in fixture management

**Technical Details:**
- Event loop fixture scope changed from function to session
- Database engine uses NullPool in test environment (TESTING=true)
- Connection timeout set to 60 seconds for CI environments
- Transaction rollback after each test for isolation
- Separate cleanup sessions to avoid transaction conflicts

## ADR-016: ChatGPT-Style Sidebar Interface Redesign

**Date:** 2025-07-24

**Status:** Accepted

**Decision:**
Redesigned the /chat page from a simple centered chat interface to a ChatGPT-style sidebar layout with thread management and default user ID.

**Context:**
User requested a more professional chat interface similar to ChatGPT, with a sidebar for managing multiple chat threads and a default user ID of "user_123" for simplified access.

**Implementation Details:**
1. **Sidebar Layout**: Left sidebar (260px width) with thread list and "New chat" button
2. **Default User**: Pre-configured with "user_123" as the default user ID
3. **Thread Management**: Automatic loading of user's existing threads on page load
4. **Visual Design**: Dark theme matching modern chat applications with proper spacing and typography
5. **Responsive Interface**: Main chat area adapts to selected thread with empty state handling
6. **Enhanced UX**: Auto-resizing textarea, proper button states, and improved message styling

**Technical Changes:**
- Complete HTML/CSS rewrite with flexbox layout and modern color scheme
- JavaScript refactored to support thread management and sidebar interaction
- Default user_123 ID eliminates setup friction
- Enhanced message display with proper role indicators and markdown rendering
- Improved WebSocket state management with visual connection indicators

**Consequences:**
- **Positive:** Professional, familiar interface similar to popular chat applications
- **Positive:** Better organization of multiple conversations through sidebar
- **Positive:** Simplified user experience with default user ID
- **Positive:** Modern dark theme reduces eye strain
- **Positive:** Enhanced usability with auto-resizing inputs and proper state management
- **Negative:** Increased frontend complexity with sidebar state management
- **Negative:** Fixed default user reduces multi-user flexibility without additional UI changes

## ADR-017: Replace Custom UUID Generation with Native crypto.randomUUID()

**Date:** 2025-07-25

**Status:** Accepted

**Decision:**
Replace custom JavaScript UUID generation function with the native `crypto.randomUUID()` method.

**Context:**
- Custom UUID generation implementation using string replacement and Math.random()
- Native `crypto.randomUUID()` is now widely supported in modern browsers
- Security and performance benefits of using native cryptographic functions

**Consequences:**
- **Positive:** Cryptographically secure UUID generation
- **Positive:** Better browser optimization and performance
- **Positive:** Reduced code complexity and maintenance
- **Positive:** Follows web standards and best practices
- **Negative:** Requires secure context (HTTPS) in production
- **Negative:** Not supported in older browsers (but acceptable for modern web apps)
