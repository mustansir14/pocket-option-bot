"""Module for Pocket Option API ssid websocket chanel."""

from pocketoptionapi.ws.channels.base import Base


class Ssid(Base):
    """Class for Pocket Option API ssid websocket chanel."""

    # pylint: disable=too-few-public-methods

    name = "ssid"

    async def __call__(self, ssid):
        """Method to send message to ssid websocket chanel.

        :param ssid: The session identifier.
        """
        await self.send_websocket_request(self.name, ssid)
