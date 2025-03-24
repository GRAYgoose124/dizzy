import asyncio
import json
import logging
import sys
import random
from pathlib import Path

from dizzy.daemon.client.asy import SimpleAsyncClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Client Setup
with open(Path(__file__).parent / "requests/new_project.json", "r") as f:
    NEW_PROJECT_REQUEST = json.load(f)


client = SimpleAsyncClient(protocol_dir=Path(__file__).parent / "custom_data", port=7777)


async def continuous_send(client_id):
    await asyncio.sleep(random.uniform(0, 1))
    # suppress logging here
    logger.info(f"Client {client_id} is about to start sending requests")
    logger.disabled = True
    while True:
        await client.send_request(NEW_PROJECT_REQUEST)
        await asyncio.sleep(random.uniform(1, 2))


async def delayed_send():
    await asyncio.sleep(2)
    response = await client.send_request(NEW_PROJECT_REQUEST)
    logger.info(f"Delayed response: {response}")


async def main():
    n_continuous_clients = 10
    await asyncio.gather(
        client.run(),
        *[continuous_send(i) for i in range(n_continuous_clients)],
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
