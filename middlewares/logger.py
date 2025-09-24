import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        logger.info(f"Request: {scope['path']}")
        await self.app(scope, receive, send)
