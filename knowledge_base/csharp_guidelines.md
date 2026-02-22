# C# Coding Guidelines

## Style & Naming
- Use PascalCase for public members, camelCase for local variables and parameters.
- Prefix interfaces with `I` (e.g. `IRepository`).
- Avoid `var` for non-obvious types; use explicit types when it aids readability.
- Keep methods under 30 lines; extract helper methods for clarity.

## Null Safety
- Enable nullable reference types (`<Nullable>enable</Nullable>`) in all new projects.
- Never suppress nullable warnings (`null!`) without a comment explaining why.
- Prefer the null-conditional operator (`?.`) and null-coalescing (`??`) over explicit null checks where the intent is "use default".
- Guard public API parameters with `ArgumentNullException.ThrowIfNull()` (.NET 6+).

## Error Handling
- Catch specific exception types; never catch bare `Exception` unless re-throwing.
- Use `try/finally` or `using` for deterministic cleanup of `IDisposable` resources.
- Log exceptions with their stack traces (`logger.LogError(ex, "…")`); do not swallow silently.
- Avoid using exceptions for control flow; prefer `TryParse` / `TryGet` patterns.

## Database
- Always use parameterised queries (`SqlCommand.Parameters.AddWithValue`). Never concatenate user input into SQL strings.
- Wrap database calls in a `using` block for `SqlConnection` and `SqlCommand`.
- Use Entity Framework or Dapper for data access; avoid raw ADO.NET unless performance-critical.
- Apply `[Required]`, `[MaxLength]`, and other data annotations on entity models.

## Security
- Never hardcode secrets (connection strings, API keys). Use `IConfiguration`, Azure Key Vault, or environment variables.
- Validate and sanitise all external input (query strings, form data, headers) before processing.
- Use `System.Security.Cryptography.RandomNumberGenerator` for cryptographic randomness, not `System.Random`.
- Avoid `BinaryFormatter` and `SoapFormatter` for deserialisation; use `System.Text.Json` or `Newtonsoft.Json`.
- Set `HttpOnly`, `Secure`, and `SameSite` attributes on cookies.

## Logging
- Use `ILogger<T>` (Microsoft.Extensions.Logging) instead of `Console.WriteLine` for application logging.
- Include structured data in log messages: `_logger.LogInformation("Order {OrderId} placed", order.Id)`.
- Never log sensitive data (passwords, tokens, PII).

## Async / Concurrency
- Prefer `async`/`await` over blocking calls (`Task.Result`, `Task.Wait()`).
- Use `ConfigureAwait(false)` in library code to avoid deadlocks.
- Use `CancellationToken` in long-running or I/O-bound operations.
- Protect shared state with `lock`, `SemaphoreSlim`, or `ConcurrentDictionary` – not raw `Monitor` unless profiling justifies it.

## Testing
- Write unit tests with xUnit, NUnit, or MSTest; aim for > 80% line coverage on business logic.
- Name tests with the pattern `MethodUnderTest_Scenario_ExpectedBehaviour`.
- Use `Moq` or `NSubstitute` for mocking dependencies.
- Keep tests independent; avoid shared mutable state between test methods.

## Dependency Management
- Keep NuGet packages up to date; run `dotnet list package --outdated` regularly.
- Pin major versions in `.csproj` to avoid breaking changes on restore.
- Prefer Microsoft-maintained packages when available.
