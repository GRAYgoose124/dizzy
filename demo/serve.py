""" A simple demo of the dizzy package. """

import logging

import asyncio
from pathlib import Path
from dizzy.daemon import Server

logging.basicConfig(level=logging.DEBUG)

# Start the server with a custom data directory
server = Server(port=7777, protocol_dir=Path(__file__).parent / "custom_data")
asyncio.run(server.run())
