## General Code Style
- All functions must have type hints for parameters and return values.
- All public functions and classes must have docstrings.
- Maximum function length should be 30 lines. If longer, refactor into smaller functions.
- Use `snake_case` for variables and functions, `PascalCase` for classes.
- Avoid magic numbers; use named constants instead.

## Logging Rules
- Never use `print()` for logging in production code. Always use the `logging` module.
- Configure logging at the application entry point, not inside library modules.
- Use appropriate log levels: DEBUG for tracing, INFO for normal flow, WARNING for recoverable issues, ERROR for failures.

## Error Handling
- Never use bare `except:` clauses. Always catch specific exceptions.
- Use custom exception classes for domain-specific errors.
- Always log exceptions with `logger.exception()` to capture the traceback.
- Do not silently swallow exceptions with `pass` inside except blocks.

## Database Rules
- Always use the `db_session` context manager for database operations. Never commit manually.
- Use parameterized queries to prevent SQL injection. Never use f-strings or `.format()` for SQL.
- Close database connections explicitly or use context managers.
- All database models must have `created_at` and `updated_at` timestamp fields.

## Security
- Do not use `subprocess` without setting `shell=False`.
- Never hardcode passwords, API keys, or secrets in source code. Use environment variables.
- Validate and sanitize all user input before processing.
- Use `secrets` module instead of `random` for generating tokens and passwords.
- Do not use `eval()` or `exec()` on user-provided data.

## Testing
- Every public function should have at least one unit test.
- Use `pytest` fixtures for test setup and teardown.
- Mock external dependencies (APIs, databases) in unit tests.
- Test both happy paths and edge cases / error conditions.

## Dependency Management
- Pin all dependency versions in `requirements.txt`.
- Do not import unused modules.
- Prefer standard library modules over third-party when functionality is equivalent.

## Concurrency
- Use `threading.Lock` or `queue.Queue` for shared mutable state.
- Prefer `concurrent.futures.ThreadPoolExecutor` over raw threads.
- Always set timeouts on network calls and thread joins.
- Avoid global mutable state in multi-threaded code.
