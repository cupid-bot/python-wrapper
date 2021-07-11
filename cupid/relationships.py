"""Model + client for a relationship between two users."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from .models import RelationshipKind, RelationshipModel

if TYPE_CHECKING:
    from .clients import BaseUserClient
    from .users import User


__all__ = ('OwnRelationship', 'Relationship')


class Relationship(RelationshipModel):
    """Relationship model with user clients instead of bare models."""

    # Sphinx makes us re-define all class attributes to change any.
    id: int
    initiator: 'User'
    other: 'User'
    kind: RelationshipKind
    accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime]


class OwnRelationship(Relationship):
    """Relationship where one of the users is the authenticated client."""

    def __init__(
            self,
            model: RelationshipModel,
            client: 'BaseUserClient',
            own_id: int):
        """Set up the model and client."""
        self.own_id = own_id
        self.opposite_id = (
            self.initiator.id if self.other.id == self.own_id
            else self.other.id
        )
        self.client = client
        super().__init__(self, **model.dict())

    async def accept(self):
        """Accept the relationship (must be a proposal)."""
        data = await self.client.accept_proposal(self.opposite_id)
        for field in data.__fields__:
            setattr(self, field, getattr(data, field))

    async def delete(self):
        """Delete the relationship.

        This rejects the relationship if it is a proposal, or leaves it if it
        has been accepted.
        """
        await self.client.leave_relationship(self.opposite_id)
