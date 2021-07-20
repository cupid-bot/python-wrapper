"""Various low-level client wrappers for the Cupid API.

The following is the inheritance tree for the client types:

                          [BaseClient]
                               |
                     UnauthenticatedClient
                               |
                     [AuthenticatedClient]
                          |        |
             [BaseUserClient]  AppClient
               |          |        |
    UserSessionClient     AppUserClient

Types marked in [brackets] are base classes not intended for direct use.
"""
from typing import Any, Literal, Optional, TYPE_CHECKING, Type, TypeVar, Union

import aiohttp
from aiohttp.client import _RequestContextManager

import pydantic

from .models import (
    AppModel,
    AppModelWithToken,
    AuthenticatedEntity,
    AuthenticatedEntityWithToken,
    BadAuthenticationError,
    ConflictError,
    CupidClientError,
    CupidServerError,
    DiscordAuthenticate,
    ForbiddenError,
    GenderUpdate,
    GraphData,
    NotFoundError,
    PaginatedUsers,
    RelationshipCreate,
    RelationshipModel,
    UserData,
    UserModel,
    UserModelWithRelationships,
    UserSearch,
    UserSessionModel,
    UserSessionModelWithToken,
    ValidationError,
)

if TYPE_CHECKING:    # pragma: no cover
    from .cupid import Cupid


__all__ = ()


T = TypeVar('T', bound=Optional[pydantic.BaseModel])


class BaseClient:
    """Cupid base client that provides utilities for making requests."""

    def __init__(self, cupid: 'Cupid'):
        """Set up the client."""
        self.cupid = cupid

    async def http_request(
            self,
            method: Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE'],
            endpoint: str,
            *,
            response_mime_type: str = 'application/json',
            **aiohttp_kwargs: Any) -> _RequestContextManager:
        """Make a request and handle the response."""
        client = await self.cupid._get_client()  # noqa: SF01
        url = f'{self.cupid.base_url}{endpoint}'
        aiohttp_kwargs['headers'] = aiohttp_kwargs.get('headers', {})
        aiohttp_kwargs['headers']['Accept'] = response_mime_type
        aiohttp_kwargs['headers']['User-Agent'] = (
            'Python-Cupid/Artemis21/AioHttp/Python3'
        )
        return client.request(method, url, **aiohttp_kwargs)

    async def handle_response(
            self,
            response: aiohttp.ClientResponse,
            data_type: Type[T]) -> T:
        """Handle a response from the API."""
        if response.status < 300:
            if data_type is None:
                return None
            data = await response.json()
            return pydantic.parse_obj_as(data_type, data)
        error = await response.json()
        if response.status >= 500:    # pragma: no cover
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

    async def request(    # noqa: CFQ002
            self,
            method: Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE'],
            endpoint: str,
            *,
            body: Optional[pydantic.BaseModel] = None,
            params: Optional[pydantic.BaseModel] = None,
            headers: Optional[dict[str, str]] = None,
            response: Type[T] = None) -> T:
        """Make a request and handle the response."""
        kwargs = {}
        if body:
            kwargs['data'] = body.json().encode()
        if params:
            kwargs['params'] = params.dict()
            for key, value in list(kwargs['params'].items()):
                # Null values should be represented by not including the key.
                if value is None:
                    del kwargs['params'][key]
        if headers:
            kwargs['headers'] = headers
        async with await self.http_request(method, endpoint, **kwargs) as resp:
            return await self.handle_response(resp, response)


class UnauthenticatedClient(BaseClient):
    """A client for making requests that don't require authentication."""

    async def discord_authenticate(
            self, auth: DiscordAuthenticate) -> UserSessionModelWithToken:
        """Create a user auth session with a Discord bearer token."""
        return await self.request(
            'POST',
            '/auth/login',
            body=auth,
            response=UserSessionModelWithToken,
        )


class AuthenticatedClient(UnauthenticatedClient):
    """Base class for clients that use some authentication."""

    def __init__(self, cupid: 'Cupid', token: str):
        """Set up the client with a token."""
        super().__init__(cupid)
        self.token = token

    async def request(self, *args: Any, **kwargs: Any) -> Any:
        """Make a request with an authorisation header."""
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['Authorization'] = f'Bearer {self.token}'
        return await super().request(*args, **kwargs)

    async def get_user(self, id: int) -> UserModelWithRelationships:
        """Get a user by ID."""
        return await self.request(
            'GET', f'/user/{id}', response=UserModelWithRelationships,
        )

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

    async def get_auth(self) -> Union[AppModel, UserSessionModel]:
        """Get the entity used to authenticate."""
        return await self.request(
            'GET',
            '/auth/me',
            response=AuthenticatedEntity,
        )

    async def delete_auth(self):
        """Delete the entity used to authenticate."""
        await self.request('DELETE', '/auth/me')

    async def refresh_token(
            self) -> Union[AppModelWithToken, UserSessionModelWithToken]:
        """Replace the token used to authenticate."""
        return await self.request(
            'PATCH',
            '/auth/me',
            response=AuthenticatedEntityWithToken,
        )


class BaseUserClient(AuthenticatedClient):
    """Base class for clients that act on behalf of a user."""

    async def propose_relationship(
            self,
            other_id: int,
            data: RelationshipCreate) -> RelationshipModel:
        """Propose a new relationship."""
        return await self.request(
            'POST',
            f'/user/{other_id}/relationship',
            body=data,
            response=RelationshipModel,
        )

    async def get_relationship(self, other_id: int) -> RelationshipModel:
        """Get a relationship you have with another user."""
        return await self.request(
            'GET',
            f'/user/{other_id}/relationship',
            response=RelationshipModel,
        )

    async def leave_relationship(self, other_id: int):
        """Delete a relationship with another user."""
        await self.request('DELETE', f'/user/{other_id}/relationship')

    async def accept_proposal(self, other_id: int) -> RelationshipModel:
        """Accept a proposal from another user."""
        return await self.request(
            'POST',
            f'/user/{other_id}/relationship/accept',
            response=RelationshipModel,
        )

    async def update_gender(self, data: GenderUpdate) -> UserModel:
        """Update the user's gender."""
        return await self.request(
            'PUT',
            '/users/me/gender',
            body=data,
            response=UserModel,
        )


class UserSessionClient(BaseUserClient):
    """A client for making requests with a user session token."""

    async def get_auth(self) -> UserSessionModel:
        """Get the session used to authenticate."""
        return await super().get_auth()

    async def refresh_token(self) -> UserSessionModelWithToken:
        """Replace the session's token."""
        return await super().refresh_token()


class AppClient(AuthenticatedClient):
    """A client for making requests as an app using an app token."""

    async def set_user(self, id: int, user: UserData) -> UserModel:
        """Create or update a user."""
        return await self.request(
            'PUT',
            f'/user/{id}',
            body=user,
            response=UserModel,
        )

    async def get_auth(self) -> AppModel:
        """Get the app used to authenticate."""
        return await super().get_auth()

    async def refresh_token(self) -> AppModelWithToken:
        """Replace the app's token."""
        return await super().refresh_token()


class AppUserClient(AppClient, BaseUserClient):
    """A client for making requests using an app token on behalf of a user."""

    def __init__(self, user_id: int, **kwargs: Any):
        """Set up the client."""
        super().__init__(**kwargs)
        self.user_id = user_id

    async def request(self, *args: Any, **kwargs: Any) -> Any:
        """Make a request with a cupid-user header."""
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['Cupid-User'] = str(self.user_id)
        return await super().request(*args, **kwargs)
