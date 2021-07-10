"""A utility for using the returned relationship graph."""
from typing import Callable

from .models import GraphData, RelationshipModel, UserModel
from .users import User


class Graph:
    """The relationship graph returned by the API."""

    def __init__(
            self,
            data: GraphData,
            get_user_client: Callable[[UserModel], User]):
        """Set up the relationship graph."""
        self.users = {
            id: get_user_client(raw)
            for id, raw in data.users.items()
        }
        self.relationships = [
            RelationshipModel(
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
