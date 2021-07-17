"""Entry class for interacting with the API."""
import aiohttp

from .auth import App, UserSession
from .clients import AppClient, UnauthenticatedClient, UserSessionClient
from .models import DiscordAuthenticate


__all__ = ('Cupid',)


class Cupid:
    """Entry class for interacting with the Cupid API.

    This is the *only* class that should be directly instantiated by code using
    this wrapper.
    """

    base_url: str

    def __init__(self, base_url: str = 'http://localhost:8080'):
        """Store the base URL of the API."""
        self.base_url = base_url
        self.http_client = None
        self._client = UnauthenticatedClient(self)

    async def _get_client(self) -> aiohttp.ClientSession:
        """Get the aiohttp client session, or create one."""
        if (not self.http_client) or self.http_client.closed:
            self.http_client = aiohttp.ClientSession()
        return self.http_client

    async def app(self, token: str) -> App:
        """Connect to the API with an app token."""
        client = AppClient(self, token)
        model = await client.get_auth()
        return App(client, model, token)

    async def user_session(self, token: str) -> UserSession:
        """Connect to the API with a user session token."""
        client = UserSessionClient(self, token)
        model = await client.get_auth()
        return UserSession(client, model, token)

    async def discord_authenticate(self, discord_token: str) -> UserSession:
        """Use a Discord OAuth2 bearer token to create a user session."""
        auth = DiscordAuthenticate(token=discord_token)
        model = await self._client.discord_authenticate(auth)
        client = UserSessionClient(self, model.token)
        return UserSession(client, model)

    async def close(self):
        """Close the underlying HTTP client and connector."""
        if self.http_client:
            await self.http_client.close()
