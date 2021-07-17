"""Combined models clients for users."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

from .models import (
    Gender,
    GenderUpdate,
    RelationshipCreate,
    RelationshipKind,
    UserData,
    UserModel,
    UserModelWithRelationships,
)
from .relationships import OwnRelationship

if TYPE_CHECKING:    # pragma: no cover
    from .clients import BaseUserClient


__all__ = (
    'User',
    'UserAsApp',
    'UserAsAppWithRelationships',
    'UserAsSelf',
    'UserAsSelfWithRelationships',
    'UserWithRelationships',
)


class BaseUserAsSelf:
    """Base class for user clients acting on their own behalf."""

    async def propose(
            self,
            other: User,
            kind: Union[RelationshipKind, str]) -> OwnRelationship:
        """Propose to another user."""
        data = RelationshipCreate(kind=kind)
        model = await self._client.propose_relationship(other.id, data)
        return OwnRelationship(self._client, model, self.id)

    async def relationship(self, other: User) -> OwnRelationship:
        """Get the user's relationship with another user."""
        model = await self._client.get_relationship(other.id)
        return OwnRelationship(self._client, model, self.id)

    async def set_gender(self, gender: Union[Gender, str]):
        """Change the user's gender."""
        data = GenderUpdate(gender=gender)
        updated = await self._client.update_gender(data)
        for field in updated.__fields__:
            setattr(self, field, getattr(updated, field))


class BaseUserAsApp(BaseUserAsSelf):
    """Base class for user clients that are authenticated with app tokens."""

    async def edit(
            self,
            *,
            name: Optional[str] = None,
            discriminator: Optional[Union[str, int]] = None,
            avatar_url: Optional[str] = None,
            gender: Optional[Union[Gender, str]] = None):
        """Update the user's information."""
        if isinstance(discriminator, int):
            discriminator = f'{discriminator:>04}'
        updated = await self._client.set_user(
            self.id,
            UserData(
                name=name or self.name,
                discriminator=discriminator or self.discriminator,
                avatar_url=avatar_url or self.avatar_url,
                gender=gender or self.gender,
            ),
        )
        for field in updated.__fields__:
            setattr(self, field, getattr(updated, field))


class User(UserModel):
    """A user model + client with no permission to do anything."""

    def __init__(self, client: 'BaseUserClient', model: UserModel):
        """Set up the user as a client and model."""
        self._client = client
        super().__init__(**model.dict())


class UserWithRelationships(User, UserModelWithRelationships):
    """A user model + client with relationships data."""

    def __init__(
            self,
            client: 'BaseUserClient',
            model: UserModelWithRelationships):
        """Set up the user as a client and model."""
        self._client = client
        UserModelWithRelationships.__init__(self, **model.dict())


class UserAsSelf(BaseUserAsSelf, User):
    """User client authenticated as itself."""


class UserAsSelfWithRelationships(BaseUserAsSelf, UserWithRelationships):
    """User client authenticated as itself, with relationship data."""


class UserAsApp(BaseUserAsApp, User):
    """User client authenticated with an app token."""


class UserAsAppWithRelationships(BaseUserAsApp, UserWithRelationships):
    """User client authenticated with an app token, with relationship data."""
