"""
Audit logging utility for tracking user actions.
"""

import logging
from typing import Optional, Dict, Any
from utils.supabase_client import get_supabase_admin_client

logger = logging.getLogger(__name__)


async def log_audit_action(
    user_id: Optional[str],
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an audit action to the audit_logs table.
    
    This function uses the Supabase service role client to insert audit records.
    It's designed to be non-blocking - if logging fails, it will log the error
    but not raise an exception that could break the main application flow.
    
    Args:
        user_id: ID of the user who performed the action (None for anonymous)
        action: Type of action (e.g., "LOGIN", "LOGOUT", "CREATE", "UPDATE", "DELETE")
        resource: Resource type affected (e.g., "user", "auth", "profile")
        resource_id: ID of the specific resource affected (optional)
        ip_address: IP address of the client
        user_agent: User agent string from the HTTP request
        metadata: Additional context data (request body, response status, etc.)
    
    Returns:
        None: This function always returns None, even if logging fails
    """
    try:
        # Get the admin client with service role key
        supabase_admin = get_supabase_admin_client()
        
        # Prepare the audit record
        audit_record = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {},
        }
        
        # Insert the audit record
        response = supabase_admin.table("audit_logs").insert(audit_record).execute()
        
        if response.data:
            logger.debug(
                "Audit log created successfully: %s %s on %s by user %s",
                action,
                resource,
                resource_id or "N/A",
                user_id or "anonymous",
            )
        else:
            logger.warning("Audit log insertion returned no data")
            
    except (ValueError, ConnectionError, TimeoutError) as e:
        # Log the error but don't raise it - audit logging should never break the app
        logger.error(
            "Failed to create audit log for action %s on %s: %s",
            action,
            resource,
            str(e),
            exc_info=True,
        )
        
        # Print to console as well for immediate visibility in development
        print(f"Audit logging error: {str(e)}")


def create_audit_metadata(
    request_body: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
    additional_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create standardized metadata for audit logs.
    
    Args:
        request_body: The request body data (for POST/PUT operations)
        status_code: HTTP response status code
        additional_data: Any additional context data
    
    Returns:
        Dict containing the metadata
    """
    metadata = {}
    
    if request_body is not None:
        # Sanitize sensitive data from request body
        sanitized_body = sanitize_request_body(request_body)
        metadata["request_body"] = sanitized_body
    
    if status_code is not None:
        metadata["status_code"] = status_code
    
    if additional_data:
        metadata.update(additional_data)
    
    return metadata


def sanitize_request_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize request body by removing sensitive fields.
    
    Args:
        body: The original request body
    
    Returns:
        Sanitized request body with sensitive fields removed
    """
    sensitive_fields = {
        "password",
        "current_password",
        "new_password",
        "confirm_password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "private_key",
    }
    
    if not isinstance(body, dict):
        return body
    
    sanitized = {}
    for key, value in body.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_request_body(value)
        else:
            sanitized[key] = value
    
    return sanitized
