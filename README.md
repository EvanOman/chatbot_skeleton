# Sample Chat App

A modern Python chat application built with FastAPI, SQLAlchemy, and WebSocket support. Features a clean domain-driven design architecture with an advanced DSPy REACT agent.

## 🚀 Features

- **Modern Architecture**: Domain-driven design with clean architecture principles
- **Real-time Chat**: WebSocket support for instant messaging
- **Advanced AI Agent**: DSPy REACT agent with sophisticated reasoning capabilities
- **Database Persistence**: PostgreSQL with SQLAlchemy 2.0 and Alembic migrations
- **Web Interface**: Built-in HTML/CSS/JavaScript frontend
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Comprehensive Testing**: Unit tests with pytest
- **Docker Support**: Containerized deployment
- **CI/CD Ready**: GitHub Actions workflows included

## 🛠 Technology Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **AI/ML**: DSPy, OpenAI API, Anthropic API
- **Database**: PostgreSQL (containerized)
- **Frontend**: HTML/CSS/JavaScript with WebSocket support
- **CLI**: Typer with Rich terminal UI
- **Package Management**: uv
- **Testing**: pytest, pytest-asyncio
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.13+
- uv (Python package manager)
- Docker & Docker Compose
- PostgreSQL (via Docker)
- OpenAI API key (optional, for advanced features)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/EvanOman/chatbot_skeleton.git
cd chatbot_skeleton
```

### 2. Install Dependencies

```bash
uv sync --extra dev
```

### 3. Start Database

```bash
docker-compose up -d
```

### 4. Run Migrations

```bash
uv run alembic upgrade head
```

### 5. Start Application

For development with **live reloading** (recommended):
```bash
uv run dev
```

Or manually:
```bash
uv run python main.py
```

The application will automatically restart when code changes are detected, providing instant feedback during development.

The application will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs  
- **ReDoc**: http://localhost:8000/redoc
- **Database GUI**: http://localhost:8080 (Adminer)

## 📖 Usage

### Web Interface

1. Open http://localhost:8000 in your browser
2. Enter a User ID or let it generate one automatically
3. Enter a Thread ID or create a new thread
4. Start chatting with the advanced AI agent!

### API Endpoints

#### Create a Thread
```bash
curl -X POST "http://localhost:8000/api/threads/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123e4567-e89b-12d3-a456-426614174000", "title": "My Chat"}'
```

#### Send a Message
```bash
curl -X POST "http://localhost:8000/api/threads/{thread_id}/messages?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, world!"}'
```

#### Get Thread Messages
```bash
curl "http://localhost:8000/api/threads/{thread_id}/messages"
```

### WebSocket Connection

Connect to `ws://localhost:8000/ws/{thread_id}/{user_id}` and send:

```json
{
  "type": "message",
  "content": "Hello via WebSocket!",
  "message_type": "text"
}
```

### Interactive CLI

The application includes a powerful command-line interface for development and testing:

```bash
# Show all available commands
uv run chatapp --help

# Check application status
uv run chatapp status

# List chat threads
uv run chatapp threads

# Quick chat with AI agent
uv run chatapp agent-chat "What is 25 * 18?"

# Create a new thread
uv run chatapp create-thread "My New Chat"

# Send a message to a thread
uv run chatapp send-message <thread-id> "Hello there!"

# Test agent capabilities
uv run chatapp test-agent --case calculator
uv run chatapp test-agent --case weather
uv run chatapp test-agent --case search

# Show development commands
uv run chatapp dev

# Database management
uv run chatapp db

# Configuration info
uv run chatapp config --show

# Application information
uv run chatapp info
```

## 🏗 Architecture

The application follows Domain-Driven Design (DDD) principles:

```
src/
├── domain/              # Core business logic
│   ├── entities/        # Domain entities (ChatThread, ChatMessage)
│   ├── repositories/    # Repository interfaces
│   └── value_objects/   # Value objects (MessageRole, ThreadStatus)
├── application/         # Application layer
│   ├── services/        # Application services (ChatService, AgentService)
│   ├── dto/            # Data transfer objects
│   └── interfaces/     # Application interfaces
├── infrastructure/      # External concerns
│   ├── database/       # SQLAlchemy models & repositories
│   ├── config/         # Configuration management
│   └── container/      # DI container setup
└── presentation/        # API layer
    ├── api/            # FastAPI routes
    ├── schemas/        # Pydantic models
    └── websocket/      # WebSocket handlers
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_basic_functionality.py -v
```

## 🔧 Development

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Database Operations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### Database Management

The project includes **Adminer**, a web-based database management tool, for easy database inspection and management during development.

**Access Database GUI:**
1. Start the services: `docker-compose up -d`
2. Open http://localhost:8080 in your browser
3. Login with the following credentials:
   - **System**: PostgreSQL
   - **Server**: postgres (auto-configured)
   - **Username**: postgres
   - **Password**: postgres
   - **Database**: chatapp

**Features:**
- Browse tables and data
- Execute SQL queries
- View table relationships
- Export/import data
- Database structure inspection
- Dark theme enabled by default

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t chat-app .

# Run with Docker Compose
docker-compose up --build
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_USERNAME` | `postgres` | Database username |
| `DB_PASSWORD` | `postgres` | Database password |
| `DB_DATABASE` | `chatapp` | Database name |
| `DB_ECHO` | `false` | Enable SQL query logging |
| `OPENAI_API_KEY` | - | OpenAI API key for advanced features |

## 📊 API Documentation

The application features comprehensive, interactive API documentation with concrete examples:

- **Swagger UI**: http://localhost:8000/docs - Interactive API testing
- **ReDoc**: http://localhost:8000/redoc - Clean documentation format

### ✨ Enhanced Documentation Features

- **Concrete Examples**: All POST/PUT endpoints include working example data
- **Try It Out**: Swagger UI examples work seamlessly with seeded database
- **Detailed Descriptions**: Each endpoint includes usage examples and tips
- **Agent Capabilities**: Examples showcase calculator, weather, and search features

### 🌱 Database Seeding

To enable the "Try It Out" examples, seed your database:

```bash
# Seed database with example data
uv run python seed_database.py

# Or use the CLI
uv run chatapp seed-db
```

The seeded data includes:
- Example users and chat threads
- Sample conversations
- Working UUIDs referenced in API documentation

## 🔬 Performance Profiling

The application includes comprehensive profiling tools for performance analysis:

### Quick Profiling Commands

```bash
# Generate interactive flame graph
uv run chatapp profile --type flamegraph --duration 30

# Profile memory usage
uv run chatapp profile --type memory --duration 60

# Generate speedscope profile for detailed analysis
uv run chatapp profile --type speedscope --duration 15

# List all generated profiles
uv run chatapp profiles

# Clean up old profiles
uv run chatapp profile-cleanup --days 7
```

### Standalone Profiling Script

```bash
# Profile running application
python profile_app.py --type flamegraph --duration 30

# Start app and profile with endpoint tests
python profile_app.py --start-app --endpoint-test --type flamegraph

# Attach to specific process
python profile_app.py --attach 1234 --type speedscope
```

### Profile Types

- **🔥 Flame Graph**: Interactive SVG showing hot code paths
- **📈 Speedscope**: JSON format for detailed call tree analysis at speedscope.app
- **🧠 Memory**: Text-based memory usage analysis
- **📊 cProfile**: Python's built-in profiler (code integration required)

### Code Integration

```python
from src.infrastructure.profiling.profiler import profile_function

@profile_function("expensive_operation")
def expensive_operation():
    # Your code here
    pass
```

## 🤖 AI Agent Features

The advanced DSPy REACT agent includes:

- **Chain-of-Thought Reasoning**: Step-by-step problem solving
- **Tool Integration**: Calculator, web search, weather, etc.
- **Conversation Memory**: Context-aware responses
- **Streaming Responses**: Real-time typing effect
- **Markdown Support**: Rich text formatting

## 🚀 CI/CD

The project includes GitHub Actions workflows for:

- **Continuous Integration**: Run tests, linting, and type checking
- **Docker Build**: Build and push Docker images to GitHub Container Registry

## 📈 Monitoring

Health check endpoint: `GET /`

The application includes built-in health checks and structured logging.

## 🔒 Security

- Input validation with Pydantic
- SQL injection protection via SQLAlchemy
- CORS configuration
- Environment-based configuration
- API key management for external services

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support, please open an issue in the GitHub repository.

---

Built with ❤️ using FastAPI, SQLAlchemy, DSPy, and modern Python practices.