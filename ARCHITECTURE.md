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

## 🏗️ **Architecture Overview**

### Domain-Driven Design Structure
```
src/
├── domain/              # Core business logic
│   ├── entities/        # Domain entities (ChatThread, ChatMessage, etc.)
│   ├── repositories/    # Repository interfaces
│   ├── services/        # Domain services
│   └── value_objects/   # Value objects
├── application/         # Application layer
│   ├── services/        # Application services
│   ├── dto/            # Data transfer objects
│   ├── interfaces/     # Application interfaces
│   └── use_cases/      # Use case implementations
├── infrastructure/      # External concerns
│   ├── database/       # SQLAlchemy models & repositories
│   ├── config/         # Configuration management
│   └── container/      # DI container setup
└── presentation/        # API layer
    ├── api/            # FastAPI routes
    ├── schemas/        # Pydantic models
    └── websocket/      # WebSocket handlers
```

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database**: PostgreSQL (containerized)
- **DI Container**: dependency-injector library
- **Frontend**: HTML/CSS/JavaScript with WebSocket support
- **Package Management**: uv

### Key Design Principles
- **Clean Architecture**: Business logic independent of frameworks
- **Dependency Injection**: Loose coupling between components
- **Repository Pattern**: Abstract data access
- **Domain-Driven Design**: Rich domain models
- **CQRS**: Separate read/write operations where beneficial

## 🚀 **Implementation Plan**

1. **Project Setup**: Dependencies and environment configuration
2. **Domain Layer**: Core entities and business logic
3. **Infrastructure**: Database models and repositories
4. **Application Layer**: Use cases and services
5. **Presentation Layer**: FastAPI routes and WebSocket handlers
6. **Frontend**: Simple chat interface
7. **Containerization**: Docker setup for PostgreSQL
8. **Testing**: Comprehensive test coverage