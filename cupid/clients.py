"""Various low-level client wrappers for the Cupid API."""
import aiohttp

import pydantic

from typing import Any, Literal, Optional, Type, TypeVar, Union

from .types import (
    App,
    AppWithToken,
    AuthenticatedEntity,
    AuthenticatedEntityWithToken,
    BadAuthenticationError,
    ConflictError,
    CupidClientError,
    CupidServerError,
    DiscordAuthenticate,
    ForbiddenError,
    GraphData,
    NotFoundError,
    PaginatedUsers,
    PartialRelationship,
    Relationship,
    Session,
    SessionWithToken,
    User,
    UserData,
    UserSearch,
    ValidationError
)


__all__ = ('AppClient', 'UnauthenticatedClient', 'UserSessionClient')


T = TypeVar('T', bound=Optional[pydantic.BaseModel])


class BaseClient(aiohttp.Client):
    """Cupid base client that provides utilities for making requests."""

    def __init__(
            self,
            *,
            base_url: str = 'http://127.0.0.1:8000'):
        """Set up the client."""
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Python-Cupid/Artemis21/AioHttp/Python3'
        }
        self.base_url = base_url

    async def get_client(self) -> aiohttp.ClientSession:
        """Get the aiohttp client session, or create one."""
        if (not self.client) or self.client.closed:
            self.client = aiohttp.ClientSession(headers=self.headers)
        return self.client

    async def handle_response(
            self,
            response: aiohttp.ClientResponse,
            data_type: Type[T]) -> T:
        """Handle a response from the API."""
        if response.status < 300:
            if data_type:
                data = await response.json()
                return data_type(**data)
            return None
        error = await response.json()
        if response.status >= 500:
            raise CupidServerError(**error)
        elif response.status == 401:
            raise BadAuthenticationError(**error)
        elif response.status == 403:
            raise ForbiddenError(**error)
        elif response.status == 404:
            raise NotFoundError(**error)
        elif response.status == 409:
            raise ConflictError(**error)
        elif response.status == 422:
            raise ValidationError(**error)
        else:
            raise CupidClientError(**error)

    async def request(
            self,
            method: Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE'],
            endpoint: str,
            *,
            body: Optional[pydantic.BaseModel] = None,
            params: Optional[pydantic.BaseModel] = None,
            response: Optional[pydantic.BaseModel] = None):
        """Make a request and handle the response."""
        client = await self.get_client()
        url = f'{self.base_url}{endpoint}'
        kwargs = {}
        if body:
            kwargs['json'] = body.dict()
        if params:
            kwargs['params'] = body.dict()
        async with client.request(method, url, **kwargs) as resp:
            return await self.handle_response(resp, response)


class UnauthenticatedClient(BaseClient):
    """A client for making requests that don't require authentication."""

    async def discord_authenticate(
            self, auth: DiscordAuthenticate) -> SessionWithToken:
        """Create a user auth session with a Discord bearer token."""
        return await self.request(
            'POST',
            '/auth/login',
            body=auth,
            response=SessionWithToken,
        )


class AuthenticatedClient(UnauthenticatedClient):
    """A client for making requests that require some authentication."""

    def __init__(self, token: str, **kwargs: Any):
        """Set up the client with a token."""
        super().__init__(**kwargs)
        self.headers['Authorization'] = f'Bearer {token}'

    async def get_user(self, id: int) -> User:
        """Get a user by ID."""
        return await self.request('GET', f'/user/{id}', response=User)

    async def get_graph(self) -> GraphData:
        """Get a graph of all users and their relationships."""
        return await self.request('GET', '/users/graph', response=GraphData)

    async def get_user_page(self, search: UserSearch) -> PaginatedUsers:
        """Get a page of user search results."""
        return await self.request(
            'GET',
            '/users/list',
            params=search,
            response=PaginatedUsers,
        )

    async def get_auth(self) -> Union[App, Session]:
        """Get the entity used to authenticate."""
        return await self.request(
            'GET',
            '/auth/me',
            response=AuthenticatedEntity,
        )

    async def delete_auth(self):
        """Delete the entity used to authenticate."""
        await self.request('DELETE', '/auth/me')

    async def refresh_token(self) -> Union[AppWithToken, SessionWithToken]:
        """Replace the token used to authenticate."""
        return await self.request(
            'PATCH',
            '/auth/me',
            response=AuthenticatedEntityWithToken,
        )


class UserSessionClient(AuthenticatedClient):
    """A client for making requests that only a user can.

    This is equivalent to an AuthenticatedClient because an app can make all
    the requests that a user can.
    """


class AppClient(AuthenticatedClient):
    """A client for making requests that only an app can."""

    async def set_user(self, id: int, user: UserData) -> User:
        """Create or update a user."""
        return await self.request(
            'PUT',
            f'/user/{id}',
            body=user,
            response=User,
        )

    async def leave_relationship(self, id: int):
        """Delete a relationship by ID."""
        await self.request('DELETE', f'/relationship/{id}')

    async def accept_proposal(self, id: int) -> Relationship:
        """Accept a proposal by ID."""
        return await self.request(
            'POST',
            f'/relationship/{id}/accept',
            response=Relationship,
        )

    async def propose_relationship(
            self, relationship: PartialRelationship) -> Relationship:
        """Propose a new relationship."""
        return await self.request(
            'POST',
            '/relationships/new',
            body=relationship,
            response=Relationship,
        )
