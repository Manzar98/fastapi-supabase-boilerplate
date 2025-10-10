# Sentry Middleware Integration Guide

This guide explains how to use the professional Sentry middleware that has been integrated into your FastAPI application.

## Overview

The Sentry middleware provides:
- **Automatic error capture**: Unhandled exceptions are automatically sent to Sentry
- **Request context**: Each error includes URL, method, headers, and user information
- **Clean error responses**: Clients receive proper JSON error responses
- **Performance monitoring**: Request timing and performance metrics
- **Centralized error handling**: No need to manually add Sentry to every route

## Configuration

### Environment Variables

Add your Sentry DSN to your `.env` file:

```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

The middleware will automatically:
- Initialize Sentry with your DSN
- Configure appropriate settings based on your environment
- Set up FastAPI and Starlette integrations

### Middleware Registration

The Sentry middleware is automatically registered in `main.py`:

```python
# Add Sentry middleware (should be early in the stack)
app.add_middleware(SentryMiddleware)
```

**Important**: The Sentry middleware should be added early in the middleware stack to capture errors from other middlewares.

## Features

### 1. Automatic Error Capture

All unhandled exceptions are automatically captured and sent to Sentry with:
- Full stack trace
- Request context (URL, method, headers)
- User information (if available)
- Request ID for tracing
- Performance metrics

### 2. Request Context

Each request gets:
- Unique request ID (`X-Request-ID` header)
- Processing time (`X-Process-Time` header)
- Full request context in Sentry

### 3. User Context

The middleware automatically extracts user information from:
- `request.state.user` (if set by auth middleware)
- Authorization headers
- Custom user context

### 4. Performance Monitoring

- Request processing time tracking
- Performance sampling (100% in development, 10% in production)
- Profile sampling for detailed performance analysis

## Usage Examples

### Basic Error Handling

Your existing error handling continues to work:

```python
@app.get("/example")
async def example_endpoint():
    try:
        # Your business logic
        result = risky_operation()
        return {"result": result}
    except ValueError as e:
        # This will be automatically captured by Sentry
        raise HTTPException(status_code=400, detail="Invalid input")
```

### Manual Error Capture

Use the `SentryErrorHandler` for manual error capture:

```python
from middlewares.sentry_middleware import SentryErrorHandler

@app.get("/manual-capture")
async def manual_capture_example(request: Request):
    try:
        # Your business logic
        result = some_operation()
        return {"result": result}
    except Exception as e:
        # Capture with additional context
        SentryErrorHandler.capture_exception(
            e,
            request=request,
            operation="some_operation",
            user_input="some_value"
        )
        raise HTTPException(status_code=500, detail="Operation failed")
```

### Adding Breadcrumbs

Add debugging breadcrumbs:

```python
from middlewares.sentry_middleware import SentryErrorHandler

@app.get("/with-breadcrumbs")
async def with_breadcrumbs():
    # Add breadcrumb for debugging
    SentryErrorHandler.add_breadcrumb(
        message="Starting important operation",
        category="operation",
        level="info",
        operation="important_task"
    )
    
    # Your business logic here
    result = perform_task()
    
    return {"result": result}
```

### Custom Messages

Capture custom messages:

```python
from middlewares.sentry_middleware import SentryErrorHandler

@app.get("/custom-message")
async def custom_message():
    # Capture a custom message
    SentryErrorHandler.capture_message(
        "Important event occurred",
        level="info",
        event_type="user_action",
        user_id="123"
    )
    
    return {"message": "Event logged"}
```

## Testing

### Test Error Capture

Visit `/sentry-debug` to trigger a test error:

```bash
curl http://localhost:8000/sentry-debug
```

This will:
1. Trigger a `ZeroDivisionError`
2. Capture it in Sentry
3. Return a proper JSON error response
4. Include request ID for tracing

### Expected Response

```json
{
  "message": "Internal server error",
  "details": "An unexpected error occurred",
  "request_id": "12345678-1234-5678-9012-123456789012"
}
```

## Error Response Format

All errors return consistent JSON responses:

```json
{
  "message": "Error description",
  "details": "Additional details",
  "request_id": "unique-request-id"
}
```

## Headers

The middleware adds these headers to responses:
- `X-Request-ID`: Unique identifier for tracing
- `X-Process-Time`: Request processing time in seconds

## Environment-Specific Behavior

### Development
- 100% error sampling
- 100% performance sampling
- Detailed logging
- Skips certain development exceptions (KeyboardInterrupt, SystemExit)

### Production
- 10% error sampling
- 10% performance sampling
- Optimized for performance
- Captures all exceptions

## Integration with Existing Code

The middleware integrates seamlessly with your existing error handling:

1. **Custom exceptions** (`AppException`) continue to work
2. **Validation errors** are handled properly
3. **General exceptions** are captured by Sentry
4. **Request IDs** are available in all error responses

## Best Practices

1. **Don't duplicate error handling**: Let the middleware handle unhandled exceptions
2. **Use manual capture sparingly**: Only for specific business logic errors
3. **Add context**: Include relevant business context when manually capturing errors
4. **Use breadcrumbs**: Add debugging breadcrumbs for complex operations
5. **Test in development**: Use `/sentry-debug` to verify Sentry integration

## Troubleshooting

### Sentry Not Capturing Errors

1. Check that `SENTRY_DSN` is set in your `.env` file
2. Verify the DSN is correct and accessible
3. Check Sentry project settings
4. Look for initialization errors in logs

### Missing Request Context

1. Ensure Sentry middleware is added early in the middleware stack
2. Check that request state is properly set by other middlewares
3. Verify user authentication middleware is working

### Performance Issues

1. Adjust sampling rates in the middleware configuration
2. Check if too many breadcrumbs are being added
3. Monitor Sentry quota usage

## Advanced Configuration

The middleware can be customized by modifying `middlewares/sentry_middleware.py`:

- Adjust sampling rates
- Modify user context extraction
- Add custom tags
- Filter events before sending
- Customize performance monitoring

For production deployments, consider:
- Setting appropriate sampling rates
- Configuring release tracking
- Setting up alerting rules in Sentry
- Monitoring Sentry quota usage
