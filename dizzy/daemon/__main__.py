import argparse
import json
import logging
from pathlib import Path
import sys
import zmq

from . import Server, Client, data_root


def server(port=5555):
    try:
        server = Server(port=port)
    except zmq.error.ZMQError as e:
        print(e)
        sys.exit(1)

    try:
        server.run()
    except KeyboardInterrupt:
        print("Server stopped.")


def client(port=5555):
    client = Client(port=port)

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
        default="INFO",
        help="Specify the logging level",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=5555,
        help="Specify the port to connect to",
    )

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.verbosity))

    if args.mode == "server":
        add_file_handler(data_root / "server.log")
        server(port=args.port)
    elif args.mode == "client":
        add_file_handler(data_root / "client.log")
        client(port=args.port)


if __name__ == "__main__":
    main()
