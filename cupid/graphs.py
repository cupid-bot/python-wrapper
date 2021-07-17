"""A utility for using the returned relationship graph."""
from typing import Callable, TYPE_CHECKING

from .models import GraphData, UserModel
from .relationships import Relationship

if TYPE_CHECKING:    # pragma: no cover
    from .users import User


__all__ = ('Graph',)


class Graph:
    """The relationship graph returned by the API."""

    users: dict[int, 'User']
    relationships: list[Relationship]

    def __init__(
            self,
            data: GraphData,
            get_user_client: Callable[[UserModel], 'User']):
        """Set up the relationship graph."""
        self.users = {
            id: get_user_client(raw)
            for id, raw in data.users.items()
        }
        self.relationships = [
            Relationship(
                id=raw.id,
                initiator=self.users[raw.initiator],
                other=self.users[raw.other],
                kind=raw.kind,
                # Only accepted relationships are shown in graphs.
                accepted=True,
                created_at=raw.created_at,
                accepted_at=raw.accepted_at,
            ) for raw in data.relationships
        ]

    # TODO: Add utility functions once we have more of an idea what we'll need.
