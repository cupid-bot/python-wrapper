"""JSON types returned or accepted by the API."""
import dataclasses
import enum
from datetime import datetime
from typing import Any, Optional, Union

import pydantic


__all__ = ('Gender', 'RelationshipKind')


class Gender(enum.Enum):
    """An enum for the gender of a user."""

    NON_BINARY = 'non_binary'
    FEMALE = 'female'
    MALE = 'male'


class RelationshipKind(enum.Enum):
    """An enum for the type of a relationship."""

    MARRIAGE = 'marriage'
    ADOPTION = 'adoption'


class UserSearch(pydantic.BaseModel):
    """Options for searching for or listing users."""

    search: Optional[str] = None
    per_page: int = 20
    page: int = 0


class DiscordAuthenticate(pydantic.BaseModel):
    """Model for a Discord authentication request."""

    token: str


class RelationshipCreate(pydantic.BaseModel):
    """Model for creating a relationship."""

    kind: RelationshipKind


class GenderUpdate(pydantic.BaseModel):
    """Model for updating a user's gender."""

    gender: Gender


class UserData(pydantic.BaseModel):
    """Data relating to a user, not including ID."""

    name: pydantic.constr(min_length=1, max_length=255)
    discriminator: pydantic.constr(regex=r'^[0-9]{4}$')    # noqa:F722
    avatar_url: pydantic.constr(min_length=7, max_length=255)
    gender: Gender


class UserModel(UserData):
    """A user as returned by the API."""

    id: int


class PartialRelationship(pydantic.BaseModel):
    """A relationship containing very minimal information."""

    # 'initiator' and 'other' are user IDs.
    initiator: int
    other: int
    kind: RelationshipKind
    created_at: datetime
    accepted_at: datetime


class RelationshipModel(pydantic.BaseModel):
    """Full data for a relationship."""

    id: int
    initiator: UserModel
    other: UserModel
    kind: RelationshipKind
    accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime]


class UserRelationships(pydantic.BaseModel):
    """All of a user's relationships."""

    accepted: list[RelationshipModel]
    incoming: list[RelationshipModel]
    outgoing: list[RelationshipModel]


class UserWithRelationships(pydantic.BaseModel):
    """A user with all of their relationships."""

    user: UserModel
    relationships: UserRelationships


class GraphData(pydantic.BaseModel):
    """Raw data for a relationship graph."""

    users: dict[int, UserModel]
    relationships: list[PartialRelationship]


class PaginatedUsers(pydantic.BaseModel):
    """One page of a paginated list of users."""

    page: int
    per_page: int
    pages: int
    total: int
    users: list[UserModel]


class UserSessionModel(pydantic.BaseModel):
    """A user authentication session."""

    id: int
    user: UserModel
    expires_at: datetime


class UserSessionModelWithToken(UserSessionModel):
    """A user authentication session including its token."""

    token: str


class AppModel(pydantic.BaseModel):
    """An API application."""

    id: int
    name: str


class AppModelWithToken(AppModel):
    """An API application including its token."""

    token: str


class AuthenticatedEntity(pydantic.BaseModel):
    """Either an API application or a user session."""

    __root__: Union[AppModel, UserSessionModel]


class AuthenticatedEntityWithToken(pydantic.BaseModel):
    """Either an API application or a user session, including its token."""

    __root__: Union[AppModelWithToken, UserSessionModelWithToken]


# Use dataclass for exceptions because inheriting from Exception and
# pydantic.BaseModel doesn't work.
# See https://github.com/samuelcolvin/pydantic/issues/1875.
@dataclasses.dataclass
class CupidError(Exception):
    """An errror returned by the API."""

    status: int
    description: str
    message: str

    def __str__(self) -> str:
        """Get a string representation for this error."""
        return f'Error {self.status}: {self.description} ({self.message}).'


class CupidClientError(CupidError):
    """Raised when the API indicates a client-caused error."""


class CupidServerError(CupidError):
    """Raised when the API indicates a server-caused error."""


class BadAuthenticationError(CupidClientError):
    """Raised when authentication is missing or invalid."""


class ForbiddenError(CupidClientError):
    """Raised when an operation is forbidden."""


class NotFoundError(CupidClientError):
    """Raised when a requested resource is not found."""


class ConflictError(CupidClientError):
    """Raised when an operation conflicts with current circumstances."""


class ValidationProblem(pydantic.BaseModel):
    """A single validation error within a document."""

    loc: list[int, str]
    msg: str
    type: str


class ValidationError(CupidClientError):
    """Raised when provided data is not valid."""

    errors: Optional[list[ValidationProblem]]

    def __init__(self, errors: Optional[list[dict[str, Any]]], **kwargs: Any):
        """Deserialise the extended error description."""
        if errors:
            errors = [ValidationProblem(**error) for error in errors]
        super().__init__(errors=errors, **kwargs)
