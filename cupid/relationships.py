"""Model + client for a relationship between two users."""
from .clients import BaseUserClient
from .models import RelationshipModel


class Relationship(RelationshipModel):
    """Model + client for a relationship between two users.

    One of the users will be the authenticated client.
    """

    def __init__(
            self,
            model: RelationshipModel,
            client: BaseUserClient,
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
