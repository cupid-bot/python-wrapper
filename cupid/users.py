"""Combined models clients for users."""
from __future__ import annotations

from typing import Optional, Union

from .clients import AppUserClient, BaseUserClient
from .models import (
    Gender,
    GenderUpdate,
    RelationshipCreate,
    RelationshipKind,
    UserData,
    UserModel,
)
from .relationships import Relationship


class User(UserModel):
    """A user model + client with no permission to do anything."""

    def __init__(self, client: BaseUserClient, model: UserModel):
        """Set up the user as a client and model."""
        self.client = client
        super().__init__(self, **model.dict())


class UserAsSelf(User):
    """A user client acting on it's own behalf."""

    async def propose(
            self,
            other: User,
            kind: Union[RelationshipKind, str]) -> Relationship:
        """Propose to another user."""
        data = RelationshipCreate(kind=kind)
        model = await self.client.propose_relationship(other.id, data)
        return Relationship(self.client, model, self.id)

    async def relationship(self, other: User) -> Relationship:
        """Get the user's relationship with another user."""
        model = await self.client.get_relationship(other.id)
        return Relationship(self.client, model, self.id)

    async def set_gender(self, gender: Union[Gender, str]):
        """Change the user's gender."""
        data = GenderUpdate(gender=gender)
        updated = await self.client.update_gender(data)
        for field in updated.__fields__:
            setattr(self, field, getattr(updated, field))


class UserAsApp(UserAsSelf):
    """A user model and client that is authenticated with an app token."""

    client: AppUserClient

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
        updated = await self.client.set_user(
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
