import zmq
import asyncio


# TODO: client/ folder for client.async and client.simple
class SimpleAsyncClient:
    def __init__(self, address="localhost", port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{address}:{port}")
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    async def send_request(self, request):
        self.socket.send(request)
        while True:
            events = await self.poller.poll()
            if events:
                if events[0][1] & zmq.POLLIN:
                    response = self.socket.recv()
                    return response
            await asyncio.sleep(0.1)  # Adjust the sleep duration as needed

    async def close(self):
        self.poller.unregister(self.socket)
        self.socket.close()
        self.context.term()


# Example usage
async def main():
    client = SimpleAsyncClient()
    response = await client.send_request(b"Hello, server!")
    print(response)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
