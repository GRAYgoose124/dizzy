""" Deprecated server / client.

```bash
$ DIZZY_DATA_ROOT="$(pwd)/dizzy/default_data" python -m dizzy.daemon server
```

```bash
$ DIZZY_DATA_ROOT="$(pwd)/dizzy/default_data" python -m dizzy.daemon client
```

"""
import argparse
import json
import logging
from pathlib import Path
import sys
import zmq
import asyncio

from . import SimpleRequestServer, SimpleCLIClient, SettingsManager
from .abstract_protocol import BaseProtocol

data_root = SettingsManager(write_to_disk=True).data_root

async def server(port=5555):
    try:
        server = SimpleRequestServer(protocol_dir=data_root, port=port)
    except zmq.error.ZMQError as e:
        print(e)
        sys.exit(1)

    try:
        await server.run()
    except KeyboardInterrupt:
        print("Server stopped.")


def client(address="localhost", port=5555):
    client = SimpleCLIClient(address=address, port=port)

    try:
        client.run()
    except KeyboardInterrupt:
        print("Client stopped.")


def add_file_handler(filename):
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.getLogger().level)
    fh.setFormatter(logging.Formatter("%(name)s\t| %(message)s"))
    logging.getLogger().addHandler(fh)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["server", "client"], help="Specify either 'server' or 'client'"
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
        help="Specify the logging level",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=5555,
        help="Specify the port to connect to",
    )
    parser.add_argument(
        "-a",
        "--address",
        default="localhost",
        help="Specify the address to connect to",
    )

    args = parser.parse_args()
    print("Using data root:", data_root)

    logging.basicConfig(
        level=getattr(logging, args.verbosity),
        format="[%(levelname)s] %(name)s:%(lineno)d: %(message)s",
    )

    if args.mode == "server":
        add_file_handler(data_root / "server.log")
        asyncio.run(server(port=args.port))
    elif args.mode == "client":
        add_file_handler(data_root / "client.log")
        asyncio.run(client(address=args.address, port=args.port))


if __name__ == "__main__":
    main()
