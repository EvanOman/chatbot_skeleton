# ADR: Unit-of-Work and Repository Pattern Implementation

**Date**: 2025-07-29  
**Status**: Implemented  
**Issue**: #25

## Context

The codebase needed implementation of the Unit-of-Work and Repository patterns to:
- Ensure atomic database transactions with fast execution (<100ms)
- Separate fast database operations from slow external operations (LLM calls)
- Provide message deduplication capabilities
- Enable proper transaction rollback on failures

## Decision

Implemented the UOW pattern with the following architecture:

### 1. Abstract Repository Interface
- `ChatRepository` ABC with async context manager protocol
- Primitive CRUD operations: `insert_thread`, `insert_message`, `get_thread`, `list_messages`
- Transaction boundaries managed by `__aenter__`/`__aexit__`

### 2. Concrete PostgreSQL Implementation
- `PgChatRepository` using async SQLAlchemy Core (not ORM)
- Connection and transaction management with proper error handling
- Message deduplication via `client_msg_id` unique constraint

### 3. Service Layer with UOW Pattern
- `UowChatService` implementing the two-transaction pattern:
  1. Fast transaction: Store user data → commit
  2. Slow operation: LLM call (outside transaction)
  3. Fast transaction: Store AI response → commit

### 4. Database Schema Changes
- Added `client_msg_id` column to `chat_message` table
- Unique partial index for deduplication (only non-null values)
- Migration file created for schema evolution

### 5. Factory Pattern for DI
- `create_chat_repository_factory()` for dependency injection
- `RepositoryContainer` for centralized configuration

## Key Design Decisions

1. **Async Interface**: Made the repository interface fully async to work with SQLAlchemy Core
2. **Short Transactions**: Each `async with repo` block is designed to complete in <100ms
3. **Error Isolation**: LLM failures don't affect committed user data
4. **Deduplication Strategy**: Optional `client_msg_id` with graceful handling of duplicates
5. **Logging**: Comprehensive logging for transaction lifecycle and errors

## Implementation Files

- `src/domain/repositories/chat_repository.py` - Abstract interface
- `src/infrastructure/database/pg_chat_repository.py` - PostgreSQL implementation
- `src/application/services/uow_chat_service.py` - Service with UOW pattern
- `src/infrastructure/database/repository_factory.py` - Factory functions
- `tests/test_uow_chat_service.py` - Comprehensive test suite
- `alembic/versions/add_client_msg_id_for_deduplication.py` - Database migration

## Benefits

- **Atomic Operations**: Proper rollback on any failure within transaction
- **Performance**: Fast database operations, slow operations outside transactions
- **Reliability**: Consistent data state even if external services fail
- **Testability**: Easy to mock repository for unit testing
- **Scalability**: Short-lived transactions reduce lock contention

## Usage Example

```python
repo_factory = create_chat_repository_factory(engine)
chat_service = UowChatService(repo_factory)

# Two separate transactions with LLM call in between
result = await chat_service.create_thread_with_first_msg(
    thread_id=uuid4(),
    user_id=user_id,
    title="New Chat",
    first_msg="Hello!",
    llm_generate_fn=my_llm_function
)
```

## Testing Strategy

- Unit tests with in-memory mock repository
- Happy path and failure scenario coverage
- Transaction rollback verification
- Deduplication behavior testing
- LLM failure isolation testing

## Limitations

1. Requires migration to add `client_msg_id` column
2. Breaking change to existing repository interfaces (now async)
3. Additional complexity compared to simple CRUD operations

## Future Considerations

- Could add read replicas for read-only operations
- Might want to add retry logic at service level
- Consider adding transaction timeout configuration
- Could implement saga pattern for complex multi-service operations