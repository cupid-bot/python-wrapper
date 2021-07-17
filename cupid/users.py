"""Combined models clients for users."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

from .models import (
    Gender,
    GenderUpdate,
    RelationshipCreate,
    RelationshipKind,
    RelationshipModel,
    UserData,
    UserModel,
    UserModelWithRelationships,
)
from .relationships import OwnRelationship, Relationship

if TYPE_CHECKING:    # pragma: no cover
    from .clients import UnauthenticatedClient


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

    def __init__(self, client: 'UnauthenticatedClient', model: UserModel):
        """Set up the user as a client and model."""
        self._client = client
        super().__init__(**model.dict())

    def __eq__(self, other: UserModel) -> bool:
        """Check if this object refers to the same user as another."""
        if not isinstance(other, UserModel):
            return False
        return self.id == other.id


class UserWithRelationships(User):
    """A user model + client with relationships data."""

    id: int
    name: str
    discriminator: str
    gender: Gender
    accepted_relationships: list[Relationship]
    incoming_proposals: list[Relationship]
    outgoing_proposals: list[Relationship]

    def __init__(
            self,
            client: 'UnauthenticatedClient',
            model: UserModelWithRelationships):
        """Set up the user as a client and model."""
        self._client = client
        load_rels = lambda models: list(map(self._load_relationship, models))
        super().__init__(
            id=model.id,
            name=model.name,
            discriminator=model.discriminator,
            gender=model.gender,
            accepted_relationships=load_rels(model.relationships.accepted),
            incoming_proposals=load_rels(model.relationships.incoming),
            outgoing_proposals=load_rels(model.relationships.outgoing),
        )

    def _load_relationship(self, model: RelationshipModel) -> Relationship:
        """Load a relationship from a model."""
        return Relationship(
            id=model.id,
            initiator=self._load_user(model.initiator),
            other=self._load_user(model.other),
            kind=model.kind,
            accepted=model.accepted,
            created_at=model.created_at,
            accepted_at=model.accepted_at,
        )

    def _load_user(self, model: UserModel) -> User:
        """Load a user from a model without relationships."""
        if model.id == self.id:
            return self
        return User(self._client, model)


class UserAsSelf(BaseUserAsSelf, User):
    """User client authenticated as itself."""


class UserAsSelfWithRelationships(BaseUserAsSelf, UserWithRelationships):
    """User client authenticated as itself, with relationship data."""


class UserAsApp(BaseUserAsApp, User):
    """User client authenticated with an app token."""


class UserAsAppWithRelationships(BaseUserAsApp, UserWithRelationships):
    """User client authenticated with an app token, with relationship data."""

    def _load_user(self, model: UserModel) -> UserAsSelf:
        """Load a user from a model without relationships."""
        if model.id == self.id:
            return self
        return UserAsApp(self._client, model)
