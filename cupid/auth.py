"""Combined models and clients for apps and user sessions."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from .clients import (
    AppClient,
    AppUserClient,
    AuthenticatedClient,
    UserSessionClient,
)
from .graphs import Graph
from .models import (
    AppModel,
    AuthenticatedEntity,
    AuthenticatedEntityWithToken,
    Gender,
    UserData,
    UserModel,
    UserModelWithRelationships,
    UserSearch,
    UserSessionModel,
)
from .pagination import UserList
from .users import (
    User,
    UserAsApp,
    UserAsAppWithRelationships,
    UserAsSelf,
    UserAsSelfWithRelationships,
    UserWithRelationships,
)


__all__ = ('App', 'UserSession')


class BaseAuth:
    """Base class for apps and clients."""

    def __init__(
            self,
            client: AuthenticatedClient,
            model: Union[AuthenticatedEntity, AuthenticatedEntityWithToken],
            token: Optional[str] = None):
        """Set up the app/session as a client."""
        self.token: str = getattr(model, 'token', token)
        self._model = model
        self._client = client

    def _get_user_client(self, user: UserModel) -> User:
        """Get a client for a user."""
        return User(self._client, self, user)

    def _get_user_client_with_relationships(
            self, user: UserModelWithRelationships) -> UserWithRelationships:
        """Get a client for a user with relationship data."""
        return UserWithRelationships(self._client, self, user)

    async def refresh_token(self):
        """Refresh the app/client's token."""
        data = await self._client.refresh_token()
        self.token = data.token
        self._client.token = data.token

    async def delete(self):
        """Delete the app/client."""
        await self._client.delete_auth()

    async def get_user(self, user_id: int) -> User:
        """Get a user by ID."""
        model = await self._client.get_user(user_id)
        return self._get_user_client_with_relationships(model)

    async def graph(self) -> Graph:
        """Get a graph of all users and their relationships."""
        return Graph(
            self._client,
            self,
            await self._client.get_graph(),
        )

    def users(
            self,
            search: Optional[str] = None,
            *,
            per_page: int = 20) -> UserList:
        """Get a page of user search results."""
        data = UserSearch(search=search, per_page=per_page)
        return UserList(self._client, data, self._get_user_client)


class App(BaseAuth):
    """An app and its associated data."""

    _client: AppClient
    _model: AppModel

    @property
    def id(self) -> int:
        """Get the app's ID."""
        return self._model.id

    @property
    def name(self) -> str:
        """Get the app's name."""
        return self._model.name

    def __eq__(self, other: App) -> bool:
        """Check if this object refers to the same app as another."""
        if not isinstance(other, App):
            return False
        return self.id == other.id

    def _get_user_client(self, user: UserModel) -> UserAsApp:
        """Get a client for a user."""
        client = AppUserClient(
            cupid=self._client.cupid, token=self.token, user_id=user.id,
        )
        return UserAsApp(client, self, user)

    def _get_user_client_with_relationships(
            self,
            user: UserModelWithRelationships) -> UserAsAppWithRelationships:
        """Get a client for a user with relationship data."""
        client = AppUserClient(
            cupid=self._client.cupid, token=self.token, user_id=user.user.id,
        )
        return UserAsAppWithRelationships(client, self, user)

    async def create_user(
            self,
            id: int,
            *,
            name: str,
            discriminator: Union[str, int, None],
            avatar_url: str,
            gender: Union[Gender, str]) -> UserAsApp:
        """Create a new user.

        If the ID is already registered, updates and returns that user.
        """
        if discriminator in (0, "0", "0000"):
            discriminator = None
        if isinstance(discriminator, int):
            discriminator = f'{discriminator:>04}'
        model = await self._client.set_user(
            id,
            UserData(
                name=name,
                discriminator=discriminator,
                avatar_url=avatar_url,
                gender=gender,
            ),
        )
        return self._get_user_client(model)


class UserSession(BaseAuth):
    """A user session and its associated data."""

    _client: UserSessionClient
    _model: UserSessionModel

    @property
    def id(self) -> int:
        """Get the session's ID."""
        return self._model.id

    @property
    def expires_at(self) -> datetime:
        """Get the time at which the session will expire."""
        return self._model.expires_at

    @property
    def user(self) -> UserAsSelf:
        """Get the user who's session this is."""
        return UserAsSelf(self._client, self, self._model.user)

    def __eq__(self, other: UserSessionModel) -> bool:
        """Check if this object refers to the same session as another."""
        if not isinstance(other, UserSessionModel):
            return False
        return self.id == other.id

    def _get_user_client(self, user: UserModel) -> Union[User, UserAsSelf]:
        """Get a client for a user."""
        if user.id == self.user.id:
            # Update our copy of the user with the new data, then return it.
            self.user._model = user  # noqa: SF01
            return self.user
        return super()._get_user_client(user)

    def _get_user_client_with_relationships(
            self,
            user: UserModelWithRelationships) -> Union[
                UserWithRelationships, UserAsSelfWithRelationships]:
        if user.user.id == self.user.id:
            self.user._model = user.user  # noqa: SF01
            return UserAsSelfWithRelationships(self._client, self, user)
        return super()._get_user_client_with_relationships(user)
