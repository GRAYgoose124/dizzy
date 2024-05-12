""" A simple client demo of the dizzy package. """

import logging

import asyncio
import time
from dizzy.daemon.client.asy import SimpleAsyncClient

logging.basicConfig(level=logging.DEBUG)

# Start the client
loop = asyncio.new_event_loop()
client = SimpleAsyncClient(port=7777)


# request and print task
async def request_task(client, entity, task):
    print(f"Request: {entity} - {task}")
    response = await client.request_task(entity, task)
    if response:
        print(
            f"Response\t->\t{'GOOD' if response['status']  == 'completed' else 'BAD'}"
        )
    else:
        print(f"Response\t->\tN/A")


async def main():
    await asyncio.gather(
        client.run(),
        client.request_task("uno", "A"),
        client.request_task("uno", "B"),
        client.request_task("uno", "C"),
    )


# start the main loop
loop.run_until_complete(main())
loop.close()
