"""Entry class for interacting with the API."""
from .auth import App, UserSession
from .clients import AppClient, UnauthenticatedClient, UserSessionClient
from .models import DiscordAuthenticate


class Cupid:
    """Entry class for interacting with the Cupid API.

    This is the *only* class that should be directly instantiated by code using
    this wrapper.
    """

    def __init__(self, base_url: str = 'http://localhost:8000'):
        """Store the base URL of the API."""
        self.base_url = base_url
        self.client = UnauthenticatedClient(self)

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
        model = await self.client.discord_authenticate(auth)
        client = UserSessionClient(self, model.token)
        return UserSession(client, model, model.token)
