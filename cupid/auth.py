"""Combined models and clients for apps and user sessions."""
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
    AppModelWithToken,
    Gender,
    UserData,
    UserModel,
    UserSearch,
    UserSessionModel,
    UserSessionModelWithToken,
)
from .pagination import UserList
from .users import User, UserAsApp, UserAsSelf


__all__ = ('App', 'UserSession')


class BaseAuth:
    """Base class for apps and clients."""

    def __init__(self, client: AuthenticatedClient):
        """Set up the app/session as a client."""
        self._client = client

    def _get_user_client(self, user: UserModel) -> User:    # pragma: no cover
        """Get a client for a user."""
        raise NotImplementedError

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
        return self._get_user_client(model)

    async def graph(self) -> Graph:
        """Get a graph of all users and their relationships."""
        return Graph(await self._client.get_graph(), self._get_user_client)

    def users(
            self, search: str, *, per_page: int = 20) -> UserList:
        """Get a page of user search results."""
        search = UserSearch(search=search, per_page=per_page)
        return UserList(self._client, search, self._get_user_client)


class App(BaseAuth, AppModelWithToken):
    """An app and its associated data."""

    def __init__(
            self,
            client: AppClient,
            model: AppModel,
            token: Optional[str] = None):
        """Set up the app as a client and model."""
        data = model.dict()
        data['token'] = data.get('token', token)
        AppModelWithToken.__init__(self, **data)
        BaseAuth.__init__(self, client)

    def _get_user_client(self, user: UserModel) -> UserAsApp:
        """Get a client for a user."""
        client = AppUserClient(
            cupid=self._client.cupid, token=self.token, user_id=user.id,
        )
        return UserAsApp(client, user)

    async def create_user(
            self,
            id: int,
            *,
            name: str,
            discriminator: Union[str, int],
            avatar_url: str,
            gender: Union[Gender, str]) -> UserAsApp:
        """Create a new user.

        If the ID is already registered, updates and returns that user.
        """
        if isinstance(discriminator, int):
            discriminator = f'{discriminator:>04}'
        model = await self._client.set_user(
            id,
            UserData(
                name=name or self.name,
                discriminator=discriminator or self.discriminator,
                avatar_url=avatar_url or self.avatar_url,
                gender=gender or self.gender,
            ),
        )
        return self._get_user_client(model)


class UserSession(UserSessionModelWithToken, BaseAuth):
    """A user session and its associated data."""

    id: int
    user: UserAsSelf
    expires_at: datetime
    token: str

    def __init__(
            self,
            client: UserSessionClient,
            model: UserSessionModel,
            token: Optional[str] = None):
        """Set up the session as a client and model."""
        data = model.dict()
        if token:
            data['token'] = token
        data['user'] = UserAsSelf(client, model.user)
        UserSessionModelWithToken.__init__(self, **data)
        BaseAuth.__init__(self, client)

    def _get_user_client(self, user: UserModel) -> User:
        """Get a client for a user."""
        if user.id == self.user.id:
            # Update our copy of the user with the new data, then return it.
            for field in user.__fields__:
                setattr(self.user, field, getattr(user, field))
            return self.user
        return User(self._client, user)
