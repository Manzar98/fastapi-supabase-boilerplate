"""
Example usage of the audit logging system.

This file demonstrates how the audit logging decorator works with FastAPI routes.
Run this script to see the audit logging in action.
"""

import asyncio
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from utils.audit_decorator import audit_action
from utils.audit_logger import log_audit_action

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple FastAPI app for demonstration
app = FastAPI(title="Audit Logging Demo")

# Example route with audit logging
@app.post("/example/create")
@audit_action("CREATE", "example")
async def create_example(
    data: dict,
    request: Request,  # noqa: ARG001
    current_user: dict = None  # Simulated user
):
    """Example route that creates something."""
    logger.info("Creating example with data: %s", data)
    return {"status": "created", "data": data}


@app.delete("/example/{example_id}")
@audit_action("DELETE", "example")
async def delete_example(
    example_id: str,
    request: Request,  # noqa: ARG001
    current_user: dict = None  # Simulated user
):
    """Example route that deletes something."""
    logger.info("Deleting example with ID: %s", example_id)
    return {"status": "deleted", "id": example_id}


@app.get("/example/{example_id}")
@audit_action("READ", "example")
async def get_example(
    example_id: str,
    request: Request,  # noqa: ARG001
    current_user: dict = None  # Simulated user
):
    """Example route that reads something."""
    logger.info("Reading example with ID: %s", example_id)
    return {"status": "found", "id": example_id}


# Direct usage example
async def direct_audit_example():
    """Example of using the audit logger directly."""
    await log_audit_action(
        user_id="user-123",
        action="MANUAL_LOG",
        resource="example",
        resource_id="example-456",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Example Browser)",
        metadata={"custom_field": "custom_value", "status_code": 200}
    )
    logger.info("Direct audit log created")


if __name__ == "__main__":
    # Test the direct audit logging
    asyncio.run(direct_audit_example())
    
    # Test the FastAPI routes
    client = TestClient(app)
    
    # Test create route
    response = client.post("/example/create", json={"name": "test", "value": 123})
    logger.info("Create response: %s", response.json())
    
    # Test delete route
    response = client.delete("/example/test-id")
    logger.info("Delete response: %s", response.json())
    
    # Test read route
    response = client.get("/example/test-id")
    logger.info("Read response: %s", response.json())
    
    logger.info("Audit logging demo completed!")
