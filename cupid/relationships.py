"""Model + client for a relationship between two users."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from .models import RelationshipKind, RelationshipModel

if TYPE_CHECKING:    # pragma: no cover
    from .auth import BaseAuth
    from .clients import AuthenticatedClient, BaseUserClient
    from .users import User


__all__ = ('OwnRelationship', 'Relationship')


class Relationship:
    """Relationship model with user clients instead of bare models."""

    def __init__(
            self,
            client: 'AuthenticatedClient',
            auth: 'BaseAuth',
            model: RelationshipModel):
        """Set up the relationship."""
        self._model = model
        self._auth = auth
        self._client = client

    @property
    def id(self) -> int:
        """Get the ID of the relationship."""
        return self._model.id

    @property
    def initiator(self) -> 'User':
        """Get the initiator of the relationship."""
        return self._auth._get_user_client(self._model.initiator)  # noqa: SF01

    @property
    def other(self) -> 'User':
        """Get the other user in the relationship."""
        return self._auth._get_user_client(self._model.other)  # noqa: SF01

    @property
    def kind(self) -> RelationshipKind:
        """Get the kind of relationship this is."""
        return self._model.kind

    @property
    def accepted(self) -> bool:
        """Check if the relationship has been accepted."""
        return self._model.accepted

    @property
    def created_at(self) -> datetime:
        """Get the time at which the relationship was proposed."""
        return self._model.created_at

    @property
    def accepted_at(self) -> Optional[datetime]:
        """Get the time at which the relationship was accepted, if any."""
        return self._model.accepted_at

    def __eq__(self, other: Relationship) -> bool:
        """Check if this object refers to the same relationship as another."""
        if not isinstance(other, Relationship):
            return False
        return self.id == other.id


class OwnRelationship(Relationship):
    """Relationship where one of the users is the authenticated client."""

    def __init__(
            self,
            client: 'BaseUserClient',
            auth: 'BaseAuth',
            model: RelationshipModel,
            own_id: int):
        """Set up the model and client."""
        super().__init__(client=client, auth=auth, model=model)
        self._own_id = own_id
        self._is_initiator = own_id == model.initiator.id
        self._opposite_id = (
            model.other.id if self._is_initiator else model.initiator.id
        )
        self._client = client

    async def accept(self):
        """Accept the relationship (must be a proposal)."""
        data = await self._client.accept_proposal(self._opposite_id)
        for field in data.__fields__:
            setattr(self, field, getattr(data, field))

    async def delete(self):
        """Delete the relationship.

        This rejects the relationship if it is a proposal, or leaves it if it
        has been accepted.
        """
        await self._client.leave_relationship(self._opposite_id)
