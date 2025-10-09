# Audit Logging System

A production-ready, decorator-based audit logging system for FastAPI applications using Supabase.

## Features

- **Decorator-based**: Simple `@audit_action()` decorator for automatic logging
- **Non-blocking**: Audit logging failures won't break your application
- **Comprehensive tracking**: Captures user actions, IP addresses, user agents, and metadata
- **Supabase integration**: Uses service role key for secure database operations
- **FastAPI compatible**: Works seamlessly with FastAPI dependency injection

## Database Setup

1. Run the SQL migration in your Supabase SQL editor:

```sql
-- See migrations/create_audit_logs_table.sql
```

This creates the `audit_logs` table with the following schema:
- `id` (UUID, primary key)
- `user_id` (UUID, nullable, foreign key to auth.users)
- `action` (TEXT) - Type of action (LOGIN, LOGOUT, CREATE, UPDATE, DELETE)
- `resource` (TEXT) - Resource type (user, auth, profile)
- `resource_id` (TEXT, nullable) - ID of specific resource affected
- `ip_address` (TEXT) - Client IP address
- `user_agent` (TEXT) - HTTP user agent string
- `metadata` (JSONB) - Additional context (request body, status code, etc.)
- `created_at` (TIMESTAMP) - When the action occurred

## Usage

### Basic Decorator Usage

```python
from fastapi import APIRouter, Request, Depends
from utils.audit_decorator import audit_action
from core.dependencies import get_current_user

router = APIRouter()

@router.post("/users")
@audit_action("CREATE", "user")
async def create_user(
    user_data: dict,
    request: Request,
    current_user=Depends(get_current_user)
):
    # Your route logic here
    return {"status": "created"}
```

### Available Decorators

The system automatically logs the following information:
- **User ID**: Extracted from `current_user` dependency (or None for anonymous)
- **IP Address**: From request headers (`x-forwarded-for`, `x-real-ip`, or direct client)
- **User Agent**: From `user-agent` header
- **Resource ID**: From path parameters (`id`, `resource_id`, etc.)
- **Request Body**: For POST/PUT operations (with sensitive data redacted)
- **Response Status**: HTTP status code

### Direct Usage

You can also use the audit logger directly:

```python
from utils.audit_logger import log_audit_action

await log_audit_action(
    user_id="user-123",
    action="CUSTOM_ACTION",
    resource="custom_resource",
    resource_id="resource-456",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    metadata={"custom_field": "value"}
)
```

## Applied Routes

The following routes have audit logging enabled:

### Authentication Routes (`api/auth.py`)
- `POST /login` - `@audit_action("LOGIN", "auth")`
- `POST /logout` - `@audit_action("LOGOUT", "auth")`
- `POST /register` - `@audit_action("REGISTER", "user")`

### User Routes (`api/user.py`)
- `PUT /profile` - `@audit_action("UPDATE", "user")`
- `DELETE /` - `@audit_action("DELETE", "user")`

## Security Features

- **Sensitive Data Redaction**: Passwords, tokens, and secrets are automatically redacted from request bodies
- **Service Role Access**: Uses Supabase service role key for secure database operations
- **Row Level Security**: Database policies ensure proper access control
- **Non-blocking Design**: Audit failures don't affect application functionality

## Configuration

Ensure your `.env` file contains:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Error Handling

The audit logging system is designed to be resilient:
- If audit logging fails, errors are logged but not raised
- The main application flow continues uninterrupted
- Failed audit attempts are logged with `_FAILED` suffix

## Querying Audit Logs

You can query audit logs using Supabase:

```sql
-- Get all login attempts
SELECT * FROM audit_logs WHERE action = 'LOGIN';

-- Get user activity for a specific user
SELECT * FROM audit_logs WHERE user_id = 'user-uuid';

-- Get recent activity
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100;

-- Get failed actions
SELECT * FROM audit_logs WHERE action LIKE '%_FAILED';
```

## Example Output

An audit log entry looks like this:

```json
{
  "id": "uuid-here",
  "user_id": "user-uuid",
  "action": "LOGIN",
  "resource": "auth",
  "resource_id": null,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "metadata": {
    "request_body": {
      "email": "user@example.com",
      "password": "[REDACTED]"
    },
    "status_code": 200
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Testing

Run the example to see the system in action:

```bash
python examples/audit_logging_demo.py
```

This will demonstrate both direct usage and decorator-based logging.
