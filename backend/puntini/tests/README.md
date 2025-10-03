# Backend Test Organization and Coverage

This document outlines the organization of the backend tests and provides an overview of their coverage.

## Test Organization

The backend tests are organized into three main categories, located in subdirectories within `backend/puntini/tests`:

-   **`unit/`**: Contains unit tests that focus on individual components in isolation. These tests are designed to be fast and are responsible for verifying the correctness of a single class or function.
-   **`integration/`**: Contains integration tests that verify the interactions between multiple components. These tests cover more complex scenarios and ensure that different parts of the system work together as expected.
-   **`e2e/`**: Intended for end-to-end (E2E) tests that simulate real user scenarios from start to finish. This directory is currently empty but is reserved for future E2E tests.

## Test Coverage

The test suite provides coverage for the following key areas of the backend:

### 1. Graph Store

-   **`InMemoryGraphStore`**: The in-memory graph database implementation is thoroughly tested with both unit and integration tests.
    -   **Unit Tests (`test_in_memory_graph.py`)**: Verify the correctness of individual methods, including node/edge operations, property updates, and deletions.
    -   **Parametrized Tests (`test_parametrized_cases.py`)**: Cover a wide range of edge cases and boundary conditions using `pytest.mark.parametrize`.
    -   **Integration Tests (`test_graph_operations.py`)**: Test complex graph scenarios, such as building and querying a social network or managing project dependencies.

### 2. API Endpoints

-   **Graph API (`test_graph_api.py`)**: The FastAPI endpoints for graph operations are tested to ensure they correctly handle requests, authentication, and data serialization.
-   **WebSocket API (`test_websocket_*.py`)**: Tests for the WebSocket connection and data types ensure that real-time communication with the frontend is reliable and that data is sent in the correct format.

### 3. Agent Orchestration

-   **`parse_goal` Node (`test_parse_goal.py`)**: The `parse_goal` node, which is the entry point for the agent's orchestration logic, is tested to ensure it correctly parses natural language goals and handles LLM interactions.
-   **`todo` Functionality (`test_todo_functionality.py`)**: The todo list feature, which is a key part of the agent's planning and execution, is tested to ensure that tasks are correctly created, tracked, and marked as complete.

### 4. Core Services

-   **Logging (`test_logging.py`, `test_logging_service.py`)**: The logging service is tested to ensure that it correctly configures handlers, avoids duplicate messages, and provides a reliable singleton instance.

### 5. Data Models

-   **API Models (`test_models.py`)**: The Pydantic models used in the API are tested to ensure they correctly handle data validation, serialization, and default values.

This comprehensive test suite ensures the reliability and correctness of the backend, providing a solid foundation for future development.