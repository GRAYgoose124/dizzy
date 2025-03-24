import logging
import asyncio
import sys
from pathlib import Path

from dizzy.daemon import SimpleRequestServer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Start the server with a custom data directory
server = None
try:
    server = SimpleRequestServer(port=7777, protocol_dir=Path(__file__).parent / "custom_data")
    logger.info ("Server initialized")
    asyncio.run(server.run())
except KeyboardInterrupt:
    logger.info("Keyboard interrupt")
except Exception as e:
    logger.exception(e)
    logger.error("Server failed to start")
    sys.exit(1)
finally:
    if server:
        logger.info("Stopping server")
        server.stop()
