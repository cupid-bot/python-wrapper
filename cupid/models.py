"""JSON types returned or accepted by the API."""
import dataclasses
import enum
from datetime import datetime
from typing import Any, Optional, Union

import pydantic


__all__ = (
    'BadAuthenticationError',
    'ConflictError',
    'CupidError',
    'CupidClientError',
    'CupidServerError',
    'ForbiddenError',
    'Gender',
    'NotFoundError',
    'RelationshipKind',
    'ValidationError',
)


class BaseModel(pydantic.BaseModel):
    """Base class for models of JSON data."""

    class Config:
        """Pydantic settings."""

        arbitrary_types_allowed = True

    def __setattr__(self, attr: str, value: Any):
        """Set a model attribute or extra attribute.

        Extra attributes, prefixed with an underscore, will not be validated
        and do not need to be declared.
        """
        if (
                attr.startswith('_')
                and (not (attr.startswith('__') and attr.endswith('__')))):
            object.__setattr__(self, attr, value)
        else:
            super().__setattr__(attr, value)


class Gender(enum.Enum):
    """An enum for the gender of a user."""

    NON_BINARY = 'non_binary'
    FEMALE = 'female'
    MALE = 'male'


class RelationshipKind(enum.Enum):
    """An enum for the type of a relationship."""

    MARRIAGE = 'marriage'
    ADOPTION = 'adoption'


class UserSearch(BaseModel):
    """Options for searching for or listing users."""

    search: Optional[str] = None
    per_page: int = 20
    page: int = 0


class DiscordAuthenticate(BaseModel):
    """Model for a Discord authentication request."""

    token: str


class RelationshipCreate(BaseModel):
    """Model for creating a relationship."""

    kind: RelationshipKind


class GenderUpdate(BaseModel):
    """Model for updating a user's gender."""

    gender: Gender


class UserData(BaseModel):
    """Data relating to a user, not including ID."""

    name: pydantic.constr(min_length=1, max_length=255)
    discriminator: pydantic.constr(regex=r'^[0-9]{4}$')    # noqa:F722
    avatar_url: pydantic.constr(min_length=7, max_length=255)
    gender: Gender


class UserModel(UserData):
    """A user as returned by the API."""

    id: int


class PartialRelationship(BaseModel):
    """A relationship containing very minimal information."""

    # 'initiator' and 'other' are user IDs.
    initiator: int
    other: int
    kind: RelationshipKind
    created_at: datetime
    accepted_at: datetime


class RelationshipModel(BaseModel):
    """Full data for a relationship."""

    id: int
    initiator: UserModel
    other: UserModel
    kind: RelationshipKind
    accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime]


class UserRelationships(BaseModel):
    """All of a user's relationships."""

    accepted: list[RelationshipModel]
    incoming: list[RelationshipModel]
    outgoing: list[RelationshipModel]


class UserModelWithRelationships(BaseModel):
    """A user with all of their relationships."""

    user: UserModel
    relationships: UserRelationships


class GraphData(BaseModel):
    """Raw data for a relationship graph."""

    users: dict[int, UserModel]
    relationships: list[PartialRelationship]


class PaginatedUsers(BaseModel):
    """One page of a paginated list of users."""

    page: int
    per_page: int
    pages: int
    total: int
    users: list[UserModel]


class UserSessionModel(BaseModel):
    """A user authentication session."""

    id: int
    user: UserModel
    expires_at: datetime


class UserSessionModelWithToken(UserSessionModel):
    """A user authentication session including its token."""

    token: str


class AppModel(BaseModel):
    """An API application."""

    id: int
    name: str


class AppModelWithToken(AppModel):
    """An API application including its token."""

    token: str


AuthenticatedEntity = Union[AppModel, UserSessionModel]
AuthenticatedEntityWithToken = Union[
    AppModelWithToken, UserSessionModelWithToken,
]


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
        description = self.description.removesuffix('.')
        message = self.message[0].lower() + self.message[1:].removesuffix('.')
        return f'Error {self.status}: {description} ({message}).'


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


class ValidationProblem(BaseModel):
    """A single validation error within a document."""

    loc: list[int, str]
    msg: str
    type: str


class ValidationError(CupidClientError):
    """Raised when provided data is not valid."""

    errors: Optional[list[ValidationProblem]] = None

    def __init__(
            self,
            errors: Optional[list[dict[str, Any]]] = None,
            **kwargs: Any):
        """Deserialise the extended error description."""
        super().__init__(**kwargs)
        if errors:
            self.errors = [ValidationProblem(**error) for error in errors]
