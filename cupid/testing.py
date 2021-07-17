"""Client for the testing endpoints of the Cupid API.

These endpoints will only be available when testing mode is enabled.
"""
import tempfile

import coverage

from .auth import App
from .clients import AppClient, BaseClient
from .cupid import Cupid
from .models import AppModelWithToken, BaseModel


class AppCreate(BaseModel):
    """Model including data for creating an app."""

    name: str


class TestingStatus(BaseModel):
    """Data returned by the server on the status of testing mode."""

    testing: bool


class RegisterDiscordToken(BaseModel):
    """Model for registering a Discord token and user for testing."""

    token: str
    id: int
    name: str
    discriminator: str
    avatar_url: str


class TestingClient(BaseClient):
    """Client for the testing endpoints of the Cupid API."""

    async def check_testing_enabled(self) -> TestingStatus:
        """Check if testing mode is enabled."""
        return await self.request('GET', '/testing', response=TestingStatus)

    async def clear_database(self):
        """Clear every table of the entire database."""
        await self.request('POST', '/testing/clear')

    async def create_app(self, data: AppCreate) -> AppModelWithToken:
        """Create a new API app."""
        return await self.request(
            'POST', '/testing/app', body=data, response=AppModelWithToken,
        )

    async def get_coverage(self) -> bytes:
        """Get the coverage report data."""
        request = await self.http_request(
            'GET',
            '/testing/coverage',
            response_mime_type='application/vnd.sqlite3',
        )
        async with request as response:
            return await response.read()

    async def register_discord_token(self, data: RegisterDiscordToken):
        """Register a Discord access token for creating a session later."""
        await self.request('POST', '/testing/discord_user', body=data)


class TestingCupid(Cupid):
    """Interact with the Cupid API including testing endpoints."""

    def __init__(self, base_url: str = 'http://localhost:8080'):
        """Store the base URL of the API."""
        super().__init__(base_url)
        self._testing_client = TestingClient(self)

    async def testing_enabled(self) -> bool:
        """Check if testing mode is enabled."""
        return (await self._testing_client.check_testing_enabled()).testing

    async def clear_database(self):
        """Clear every table of the entire database."""
        await self._testing_client.clear_database()

    async def create_app(self, name: str) -> App:
        """Create a new API app."""
        model = await self._testing_client.create_app(AppCreate(name=name))
        client = AppClient(self, model.token)
        return App(client, model)

    async def register_discord_token(
            self,
            token: str,
            *,
            id: int,
            name: str,
            discriminator: str,
            avatar_url: str):
        """Register a Discord access token for creating a session later."""
        data = RegisterDiscordToken(
            token=token,
            id=id,
            name=name,
            discriminator=discriminator,
            avatar_url=avatar_url,
        )
        await self._testing_client.register_discord_token(data)

    async def coverage(self) -> coverage.Coverage:
        """Get a code coverage report for the API server."""
        data = await self._testing_client.get_coverage()
        filename = tempfile.mkstemp()[1]
        with open(filename, 'wb') as file:
            file.write(data)
        cov = coverage.Coverage(filename)
        cov.load()
        return cov
