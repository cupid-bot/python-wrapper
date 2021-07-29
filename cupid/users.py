"""Combined models clients for users."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

from . import relationships
from .graphs import Graph
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
    from .auth import BaseAuth
    from .clients import AppUserClient, AuthenticatedClient, BaseUserClient


__all__ = (
    'User',
    'UserAsApp',
    'UserAsAppWithRelationships',
    'UserAsSelf',
    'UserAsSelfWithRelationships',
    'UserWithRelationships',
)


class User:
    """A user model + client with no permission to do anything."""

    def __init__(
            self,
            client: 'AuthenticatedClient',
            auth: 'BaseAuth',
            model: UserModel):
        """Set up the user as a client and model."""
        self._model = model
        self._auth = auth
        self._client = client

    @property
    def id(self) -> int:
        """Get the app's ID."""
        return self._model.id

    @property
    def name(self) -> str:
        """Get the user's name."""
        return self._model.name

    @property
    def discriminator(self) -> str:
        """Get the user's discriminator."""
        return self._model.discriminator

    @property
    def avatar_url(self) -> str:
        """Get the user's avatar URL."""
        return self._model.avatar_url

    @property
    def gender(self) -> Gender:
        """Get the user's gender."""
        return self._model.gender

    def __eq__(self, other: User) -> bool:
        """Check if this object refers to the same user as another."""
        if not isinstance(other, User):
            return False
        return self.id == other.id

    async def graph(self) -> Graph:
        """Get a graph of all users related (even distantly) to this one."""
        return Graph(
            self._client,
            self._auth,
            await self._client.get_user_graph(self.id),
        )


class UserAsSelf(User):
    """Base class for user clients acting on their own behalf."""

    _client: 'BaseUserClient'

    async def propose(
            self,
            other: User,
            kind: Union[RelationshipKind, str]) -> 'OwnRelationship':
        """Propose to another user."""
        data = RelationshipCreate(kind=kind)
        model = await self._client.propose_relationship(other.id, data)
        return relationships.OwnRelationship(
            self._client, self._auth, model, self.id,
        )

    async def relationship(self, other: User) -> 'OwnRelationship':
        """Get the user's relationship with another user."""
        model = await self._client.get_relationship(other.id)
        return relationships.OwnRelationship(
            self._client, self._auth, model, self.id,
        )

    async def set_gender(self, gender: Union[Gender, str]):
        """Change the user's gender."""
        data = GenderUpdate(gender=gender)
        self._model = await self._client.update_gender(data)


class UserAsApp(UserAsSelf):
    """Base class for user clients that are authenticated with app tokens."""

    _client: AppUserClient

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
        self._model = await self._client.set_user(
            self.id,
            UserData(
                name=name or self.name,
                discriminator=discriminator or self.discriminator,
                avatar_url=avatar_url or self.avatar_url,
                gender=gender or self.gender,
            ),
        )


class UserWithRelationships(User):
    """A user model + client with relationships data."""

    def __init__(
            self,
            client: 'AuthenticatedClient',
            auth: 'BaseAuth',
            model: UserModelWithRelationships):
        """Set up the user as a client and model."""
        super().__init__(client, auth, model.user)
        self._model_with_relationships = model

    @property
    def accepted_relationships(self) -> list['Relationship']:
        """Get a list of the user's accepted relationships."""
        return self._load_relationships(
            self._model_with_relationships.relationships.accepted,
        )

    @property
    def incoming_proposals(self) -> list['Relationship']:
        """Get a list of the user's incoming proposals."""
        return self._load_relationships(
            self._model_with_relationships.relationships.incoming,
        )

    @property
    def outgoing_proposals(self) -> list['Relationship']:
        """Get a list of the user's outgoing proposals."""
        return self._load_relationships(
            self._model_with_relationships.relationships.outgoing,
        )

    def _load_relationships(
            self, models: list[RelationshipModel]) -> list['Relationship']:
        """Load a list of relationships from models."""
        return list(map(self._load_relationship, models))

    def _load_relationship(
            self, model: RelationshipModel) -> 'Relationship':
        """Load a relationship from a model."""
        return Relationship(
            client=self._client,
            auth=self._auth,
            model=model,
        )


class UserAsSelfWithRelationships(UserAsSelf, UserWithRelationships):
    """User client authenticated with an app token, with relationship data."""

    def _load_relationship(
            self, model: RelationshipModel) -> 'OwnRelationship':
        """Load a relationship from a model."""
        return OwnRelationship(
            client=self._client,
            auth=self._auth,
            model=model,
            own_id=self.id,
        )


class UserAsAppWithRelationships(UserAsApp, UserAsSelfWithRelationships):
    """User client authenticated with an app token, with relationship data."""
