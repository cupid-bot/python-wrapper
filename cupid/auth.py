"""Combined models and clients for apps and user sessions."""
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
    UserModel,
    UserSearch,
    UserSessionModel,
    UserSessionModelWithToken,
)
from .pagination import UserList
from .users import User, UserAsApp, UserAsSelf


class BaseAuth:
    """Base class for apps and clients."""

    def __init__(self, client: AuthenticatedClient):
        """Set up the app/session as a client."""
        self.client = client

    def _get_user_client(self, user: UserModel) -> User:
        """Get a client for a user."""
        raise NotImplementedError

    async def refresh_token(self):
        """Refresh the app/client's token."""
        data = await self.client.refresh_token()
        self.token = data.token
        self.client.token = data.token

    async def delete(self):
        """Delete the app/client."""
        await self.client.delete_auth()

    async def user(self, user_id: int) -> User:
        """Get a user by ID."""
        model = await self.client.get_user(user_id)
        return self._get_user_client(model)

    async def graph(self) -> Graph:
        """Get a graph of all users and their relationships."""
        return Graph(await self.client.get_graph(), self._get_user_client)

    def users(
            self, search: str, *, per_page: int = 20) -> UserList:
        """Get a page of user search results."""
        search = UserSearch(search=search, per_page=per_page)
        return UserList(self.client, search, self._get_user_client)


class App(BaseAuth, AppModelWithToken):
    """An app and it's associated data."""

    def __init__(self, client: AppClient, model: AppModel, token: str):
        """Set up the app as a client and model."""
        BaseAuth.__init__(self, client)
        AppModelWithToken.__init__(self, **model.dict(), token=token)

    def get_user_client(self, user: UserModel) -> UserAsApp:
        """Get a client for a user."""
        client = AppUserClient(token=self.token, user_id=user.id)
        return UserAsApp(client, user)


class UserSession(BaseAuth, UserSessionModelWithToken):
    """A user session and it's associated data."""

    def __init__(
            self,
            client: UserSessionClient,
            model: UserSessionModel,
            token: str):
        """Set up the session as a client and model."""
        BaseAuth.__init__(self, client)
        UserSessionModelWithToken.__init__(self, **model.dict(), token=token)
        self.user = UserAsSelf(client, self.user)

    def get_user_client(self, user: UserModel) -> User:
        """Get a client for a user."""
        if user.id == self.user.id:
            # Update our copy of the user with the new data, then return it.
            for field in user.__fields__:
                setattr(self.user, field, getattr(user, field))
            return self.user
        return User(self.client, user)
