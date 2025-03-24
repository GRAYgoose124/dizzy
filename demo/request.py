import asyncio
import json
import logging
import sys
from pathlib import Path

from dizzy.daemon.client.asy import SimpleAsyncClient
from the_protocol import DefaultProtocol

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Client Setup
with open(Path(__file__).parent / "requests/new_project.json", "r") as f:
    NEW_PROJECT_REQUEST = json.load(f)


client = SimpleAsyncClient(protocol=DefaultProtocol, port=7777)


async def continuous_send():
    await asyncio.sleep(1)
    while True:
        logger.info("Sending new project request")
        await client.send_request(NEW_PROJECT_REQUEST)
        await asyncio.sleep(5)


async def delayed_send():
    await asyncio.sleep(2)
    response = await client.send_request(NEW_PROJECT_REQUEST)
    logger.info(f"Delayed response: {response}")


async def main():
    await asyncio.gather(
        client.run(),
        continuous_send(),
        delayed_send(),
    )


# Adjust the event loop handling to use the default loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    logger.info("Keyboard interrupt")
except Exception as e:
    logger.exception(e)
    logger.error("Client failed to start")
    sys.exit(1)
finally:
    client.stop()
