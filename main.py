import asyncio
from nats.aio.client import Client as NATS, Msg as msg, Subscription as Sub, Awaitable as awaitable, Type as type
import signal
import sys


class App(object):
    def __init__(self):
        self.nc = NATS()
        self.sub = None
        self.shutdown = False
        # Registering the signals
        signal.signal(signal.SIGINT, self.exit_graceful)
        signal.signal(signal.SIGTERM, self.exit_graceful)

    nc = NATS
    sub = Sub

    def exit_graceful(self, signum, frame):
        print('Received:', signum, ": ", frame)
        self.shutdown = True

    async def connect_to_nats(self):
        await self.nc.connect("nats://127.0.0.1:4222")

    async def set_up_subscriptions(self):

        self.sub = await self.nc.subscribe("auth.generate.password", cb=self.process_request)

    async def process_request(self, m=type[msg]) -> awaitable[None] | None:
        print(f"Received a message on '{m.subject} {m.reply}': {m.data.decode()}")
        return await self.nc.publish(m.reply, b'secretpassword')

    async def run(self):
        print("running App: ")

        while True:
            await asyncio.sleep(1)

    async def stop(self):
        # Remove interest in subscription.
        await self.nc.flush()
        print("nats conn terminating...")
        # Terminate connection to NATS.
        await self.nc.drain()


async def main():
    app = App()

    _ = asyncio.gather(app.connect_to_nats(), app.set_up_subscriptions())

    while not app.shutdown:
        await app.run()

    await app.stop()
    sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())
