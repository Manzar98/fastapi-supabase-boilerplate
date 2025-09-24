"""
Logger middleware for FastAPI.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggerMiddleware:
    """
    Middleware to log incoming requests.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        logger.info("Request: %s", scope["path"])
        await self.app(scope, receive, send)
