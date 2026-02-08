import asyncio
from agentbay import AgentBay
from agentbay.session_params import CreateSessionParams
from agentbay.browser.browser import BrowserOption
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AgentBayService:
    def __init__(self):
        self.api_key = settings.AGENTBAY_API_KEY
        self.client = AgentBay(api_key=self.api_key)
        self.session = None

    def start_session_sync(self):
        """Starts an AgentBay session (sync call for client.create which is likely sync)."""
        logger.info("Creating AgentBay session...")
        # Note: client.create is synchronous in the SDK based on docs seen
        params = CreateSessionParams(image_id="browser_latest")
        result = self.client.create(params)
        
        if not result.success:
            err = result.message if hasattr(result, 'message') else 'Unknown error'
            logger.error(f"Failed to create AgentBay session: {err}")
            raise Exception(f"Failed to create AgentBay session: {err}")
            
        self.session = result.session
        logger.info(f"AgentBay session created: {self.session.session_id}")
        return self.session

    async def initialize_browser(self):
        """Initializes the browser in the remote session and returns the CDP URL."""
        if not self.session:
            raise Exception("Session not started")
        
        logger.info("Initializing remote browser...")
        option = BrowserOption()
        
        # initialize_async is an async method on session.browser
        success = await self.session.browser.initialize_async(option)
        if not success:
             raise Exception("Failed to initialize remote browser")
             
        endpoint = self.session.browser.get_endpoint_url()
        logger.info(f"Browser initialized. CDP Endpoint: {endpoint}")
        return endpoint

    def close_session(self):
        """Terminates the session."""
        if self.session:
            try:
                self.client.delete(self.session)
                logger.info("AgentBay session terminated.")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
            finally:
                self.session = None
