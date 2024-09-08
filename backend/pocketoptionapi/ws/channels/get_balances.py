import time

from pocketoptionapi.ws.channels.base import Base


class Get_Balances(Base):
    name = "sendMessage"

    async def __call__(self):
        """
        :param options_ids: list or int
        """

        data = {"name": "get-balances", "version": "1.0"}
        print("get_balances in get_balances.py")

        await self.send_websocket_request(self.name, data)
