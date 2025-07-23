# Modern Python Chat Application Architecture

## 🗄️ **Database Schema**

### Chat Thread Table
```sql
CREATE TABLE chat_thread (
    thread_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL, -- Foreign key to user table
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active', -- active, archived, deleted, etc.
    title       TEXT,
    summary     TEXT,
    metadata    JSONB,
    UNIQUE (user_id, thread_id)
);

CREATE INDEX idx_chat_thread_user ON chat_thread (user_id);
```

### Chat Message Table
```sql
CREATE TABLE chat_message (
    message_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id    UUID NOT NULL REFERENCES chat_thread(thread_id) ON DELETE CASCADE,
    user_id      UUID NOT NULL, -- Sender (user or AI system)
    role         TEXT NOT NULL CHECK (role IN ('user', 'ai', 'system')), -- who sent the message
    content      TEXT NOT NULL,
    type         TEXT NOT NULL DEFAULT 'text', -- text, plot, table, error, etc.
    metadata     JSONB,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_chat_message_thread ON chat_message (thread_id, created_at);
```

### Chat Attachment Table
```sql
CREATE TABLE chat_attachment (
    attachment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id    UUID NOT NULL REFERENCES chat_message(message_id) ON DELETE CASCADE,
    thread_id     UUID NOT NULL REFERENCES chat_thread(thread_id) ON DELETE CASCADE,
    url           TEXT NOT NULL,
    file_type     TEXT, -- e.g. plotly-json, csv, img, etc.
    metadata      JSONB,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_chat_attachment_thread ON chat_attachment (thread_id);
```

## 🏗️ **Current Architecture Overview**

### Domain-Driven Design Structure
```
src/
├── domain/              # Core business logic
│   ├── entities/        # Domain entities (ChatThread, ChatMessage, etc.)
│   ├── repositories/    # Repository interfaces
│   ├── services/        # Domain services
│   └── value_objects/   # Value objects (MessageRole, ThreadStatus)
├── application/         # Application layer
│   ├── services/        # Application services (ChatService, AgentService)
│   ├── dto/            # Data transfer objects
│   └── interfaces/     # Application interfaces
├── infrastructure/      # External concerns
│   ├── database/       # SQLAlchemy models & repositories
│   ├── config/         # Configuration management
│   ├── container/      # DI container setup
│   └── profiling/      # Performance monitoring
└── presentation/        # API layer
    ├── api/            # FastAPI routes (chat, export, visualization, webhooks)
    ├── schemas/        # Pydantic models
    └── websocket/      # WebSocket handlers
```

## 🤖 **AI Agent Architecture**

### DSPy REACT Agent System
The application features a sophisticated AI agent built using the DSPy REACT (Reasoning and Acting) pattern:

```python
# Core Agent Components
- ReasoningModule: Chain-of-thought reasoning
- ActionModule: Tool selection and execution
- ObservationModule: Tool result processing
- MemoryModule: Context and conversation history
```

### Agent Tools Ecosystem
```python
Available Tools:
├── Calculator          # Mathematical computations with natural language
├── TextProcessor      # Text analysis and manipulation
├── MemoryTool         # BM25-based conversation memory
├── FileProcessor      # File operations and analysis
├── WebSearch          # Internet search (SerpAPI/DuckDuckGo)
├── WeatherTool        # Weather information (OpenWeatherMap)
└── CodeExecutor       # Safe code execution sandbox
```

### Memory System Architecture
```python
BM25 Memory System:
├── Storage Layer      # Persistent memory storage
├── Retrieval Engine   # BM25Okapi algorithm for relevance
├── Tokenization      # NLTK-based text processing
└── Context Manager    # Conversation context maintenance
```

## 🔧 **Technology Stack**

### Backend Technologies
- **Framework**: FastAPI with WebSocket support
- **Database**: PostgreSQL with SQLAlchemy 2.0 and AsyncPG
- **AI/ML**: DSPy framework with OpenAI/Anthropic integration
- **Search**: BM25Okapi with NLTK tokenization
- **Memory**: Rank-BM25 for information retrieval
- **CLI**: Typer with Rich terminal formatting
- **Profiling**: py-spy with flame graph generation

### Infrastructure & Deployment
- **Containerization**: Docker with multi-stage builds
- **Database GUI**: Adminer web interface
- **Package Management**: uv (modern pip replacement)
- **Migration System**: Alembic for schema versioning
- **Health Checks**: HTTP endpoint monitoring

### Development & Monitoring
- **Live Reloading**: Automatic server restart on code changes
- **Rich Logging**: Colorized request/response logging
- **Performance Monitoring**: Integrated profiling with visualization
- **API Documentation**: Enhanced Swagger/ReDoc with examples
- **Code Quality**: Black, Ruff, MyPy with automated formatting

## 🌐 **API Architecture**

### RESTful Endpoints
```
Core Chat API:
├── /api/threads/              # Thread management
├── /api/threads/{id}/messages # Message operations
├── /api/export/              # Multi-format data export
├── /api/visualization/       # Conversation tree visualization
├── /api/webhooks/           # External integrations
├── /api/profiling/          # Performance analysis
└── /api/dashboard/          # Developer tools
```

### WebSocket Integration
```python
Real-time Communication:
├── Connection: ws://host/ws/{thread_id}/{user_id}
├── Message Types: text, system, tool_use, streaming
├── Streaming Support: Real-time response generation
└── Error Handling: Graceful disconnection and reconnection
```

## 🔍 **Data Flow Architecture**

### Request Processing Pipeline
```
1. HTTP/WebSocket Request → FastAPI Router
2. Request Validation → Pydantic Schemas
3. Dependency Injection → Service Layer
4. Business Logic → Domain Services
5. Data Persistence → Repository Pattern
6. AI Processing → DSPy REACT Agent
7. Response Generation → Streaming/Standard
8. Client Delivery → WebSocket/HTTP
```

### Agent Processing Flow
```
1. User Input → Message Processing
2. Context Retrieval → Memory System (BM25)
3. Reasoning Phase → Chain-of-thought analysis
4. Tool Selection → Available tool evaluation
5. Tool Execution → External API calls/computations
6. Result Processing → Response synthesis
7. Memory Storage → Conversation persistence
8. Response Streaming → Real-time delivery
```

## 🚀 **Key Design Principles**

### Architectural Patterns
- **Clean Architecture**: Business logic independent of frameworks
- **Domain-Driven Design**: Rich domain models with clear boundaries
- **Repository Pattern**: Abstract data access with interface segregation
- **Dependency Injection**: Loose coupling with testable components
- **CQRS**: Separate read/write operations where beneficial

### Performance Considerations
- **Async/Await**: Full asynchronous request handling
- **Connection Pooling**: Database connection optimization
- **Streaming Responses**: Real-time user experience
- **Memory Management**: Efficient conversation context handling
- **Caching Strategy**: BM25 index caching for fast retrieval

### Security & Reliability
- **Input Validation**: Pydantic model validation at API boundaries
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **API Key Management**: Environment-based configuration
- **Error Handling**: Graceful degradation with fallback mechanisms
- **Health Monitoring**: Application health checks and logging

## 📊 **Current Implementation Status**

### ✅ Completed Components
- Core chat functionality with database persistence
- Advanced DSPy REACT agent with tool integration
- Real-time WebSocket communication with streaming
- Comprehensive CLI with 15+ management commands
- Interactive API documentation with concrete examples
- Performance profiling with flame graph visualization
- Conversation tree visualization with D3.js
- Multi-format export functionality (JSON, CSV, Markdown, HTML)
- Webhook system for external integrations
- Database GUI integration with Adminer
- Live reloading development environment
- Rich logging with colorized output
- Docker containerization with health checks
- GitHub Actions CI/CD pipeline

### 🔧 Extension Points
The architecture supports easy extension through:
- **Plugin System**: New tools can be added to the agent ecosystem
- **Custom Repositories**: Alternative database implementations
- **Additional Export Formats**: Extensible export system
- **Webhook Handlers**: Custom integration endpoints
- **Profiling Plugins**: Additional monitoring capabilities

---

**Architecture Status**: ✅ **PRODUCTION READY**
**Last Updated**: 2025-07-23
**Design Philosophy**: Clean, modular, and extensible with modern Python practices
