import asyncio
import json
import logging
from pathlib import Path

from dizzy.daemon.client.asy import SimpleAsyncClient
from dizzy.daemon.abstract_protocol import DefaultProtocol

logging.basicConfig(level=logging.DEBUG)

# Client Setup
with open(Path(__file__).parent / "requests/new_project.json", "r") as f:
    NEW_PROJECT_REQUEST = json.load(f)

client = SimpleAsyncClient(protocol=DefaultProtocol, port=7777)


async def continuous_send():
    while True:
        print("Sending new project request")
        await client.send_request(NEW_PROJECT_REQUEST)
        await asyncio.sleep(5)


async def delayed_send():
    await asyncio.sleep(3)
    response = await client.send_request(NEW_PROJECT_REQUEST)
    print(f"Delayed response: {response}")


async def main():
    with open(Path(__file__).parent / "requests/new_project.json", "r") as f:
        NEW_PROJECT_REQUEST = json.load(f)

    # Run the client, send an initial request, and then start continuous sending
    await asyncio.gather(
        client.run(),
        continuous_send(),
        delayed_send(),
    )


# Adjust the event loop handling to use the default loop
asyncio.run(main())
