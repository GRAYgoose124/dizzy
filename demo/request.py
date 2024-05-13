import asyncio
import json
import logging
from pathlib import Path
from dizzy.daemon.client.asy import SimpleAsyncClient

logging.basicConfig(level=logging.DEBUG)

# Client Setup
client = SimpleAsyncClient(port=7777)


async def continuous_send():
    with open(Path(__file__).parent / "requests/new_project.json", "r") as f:
        NEW_PROJECT_REQUEST = json.load(f)
    while True:
        print("Sending new project request")
        await client.send_request(NEW_PROJECT_REQUEST)
        await asyncio.sleep(3)


async def main():
    with open(Path(__file__).parent / "requests/new_project.json", "r") as f:
        NEW_PROJECT_REQUEST = json.load(f)

    # Run the client, send an initial request, and then start continuous sending
    await asyncio.gather(
        client.run(),
        client.send_request(NEW_PROJECT_REQUEST),
        continuous_send(),
    )


# Adjust the event loop handling to use the default loop
asyncio.run(main())
