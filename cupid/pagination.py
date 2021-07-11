"""Tool for paginating a list of user results."""
from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .clients import AuthenticatedClient
    from .models import UserModel, UserSearch
    from .users import User


__all__ = ('UserList',)


class UserList:
    """An iterable of users matching a query."""

    def __init__(
            self,
            client: 'AuthenticatedClient',
            search: 'UserSearch',
            get_user_client: Callable[['UserModel'], 'User']):
        """Set up the paginator."""
        self.client = client
        self.search = search
        self._get_user_client = get_user_client
        self.total_results = search.per_page    # Meaningless default.

    def __len__(self) -> int:
        """Get the number of users in the full list.

        Until a request has been made (using `async for`, `get_page` or
        `flatten`), this will return a meaningless default.
        """
        return self.total_results

    async def get_page(self, page: int = 0) -> list['User']:
        """Get a specific page of results."""
        self.search.page = page
        raw = await self.client.get_user_page(self.search)
        self.total_results = raw.total
        return list(map(self._get_user_client, raw.users))

    async def flatten(self, limit: Optional[int] = None) -> list['User']:
        """Get the full list of users.

        `limit` is a limit to the number of results to fetch.
        """
        users = []
        page = 0
        while True:
            new_page = await self.get_page(page)
            if not new_page:
                return users
            users.extend(new_page)
            if limit and limit >= len(users):
                return users[:limit]
            page += 1

    def __aiter__(self) -> UserListPaginator:
        """Iterate over the users."""
        return UserListPaginator(self)


class UserListPaginator:
    """An iterator over a list of users."""

    def __init__(self, user_list: UserList):
        """Set up the iterator."""
        self.user_list = user_list
        self.page = 0
        self.user_cache = []

    async def __anext__(self) -> 'User':
        """Get the next user in the list."""
        if not self.user_cache:
            self.user_cache = await self.user_list.get_page(self.page)
            self.page += 1
        if not self.user_cache:
            # If we didn't get anything, we've reached the end.
            raise StopAsyncIteration
        return self.user_cache.pop(0)
