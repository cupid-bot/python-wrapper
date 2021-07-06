"""JSON types returned or accepted by the API."""
import enum
import pydantic
from datetime import datetime
from typing import Optional, Union


__all__ = (
    'App',
    'AppWithToken',
    'AuthenticatedEntity',
    'AuthenticatedEntityWithToken',
    'BadAuthenticationError',
    'ConflictError',
    'CupidClientError',
    'CupidError',
    'CupidServerError',
    'DiscordAuthenticate',
    'ForbiddenError',
    'Gender',
    'GraphData',
    'NotFoundError',
    'PaginatedUsers',
    'PartialRelationship',
    'Relationship',
    'RelationshipKind',
    'Session',
    'SessionWithToken',
    'User',
    'UserData',
    'UserSearch',
    'ValidationError',
    'ValidationProblem',
)


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


class UserData(pydantic.BaseModel):
    """Data relating to a user, not including ID."""

    name: pydantic.constr(min_length=1, max_length=255)
    discriminator: pydantic.constr(regex=r'^[0-9]{4}$')    # noqa:F722
    avatar_url: pydantic.constr(min_length=7, max_length=255)
    gender: Gender


class User(UserData):
    """A user as returned by the API."""

    id: int


class PartialRelationship(pydantic.BaseModel):
    """A relationship containing very minimal information."""

    # 'initiator' and 'other' are user IDs.
    initiator: int
    other: int
    kind: RelationshipKind


class Relationship(pydantic.BaseModel):
    """Full data for a relationship."""

    id: int
    initiator: User
    other: User
    kind: RelationshipKind
    accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime]


class GraphData(pydantic.BaseModel):
    """Raw data for a relationship graph."""

    users: dict[int, User]
    relationships: list[PartialRelationship]


class PaginatedUsers(pydantic.BaseModel):
    """One page of a paginated list of users."""

    page: int
    per_page: int
    pages: int
    total: int
    users: list[User]


class Session(pydantic.BaseModel):
    """A user authentication session."""

    id: int
    user: User
    expires_at: datetime


class SessionWithToken(Session):
    """A user authentication session including it's token."""

    token: str


class App(pydantic.BaseModel):
    """An API application."""

    id: int
    name: str


class AppWithToken(App):
    """An API application including it's token."""

    token: str


class AuthenticatedEntity(pydantic.BaseModel):
    """Either an API application or a user session."""

    __root__: Union[App, Session]


class AuthenticatedEntityWithToken(pydantic.BaseModel):
    """Either an API application or a user session, including it's token."""

    __root__: Union[AppWithToken, SessionWithToken]


class CupidError(Exception, pydantic.BaseModel):
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


class ValidationProblem(pydantic.BaseModel):
    """A single validation error within a document."""

    loc: list[int, str]
    msg: str
    type: str


class BadAuthenticationError(CupidClientError):
    """Raised when authentication is missing or invalid."""


class ForbiddenError(CupidClientError):
    """Raised when an operation is forbidden."""


class NotFoundError(CupidClientError):
    """Raised when a requested resource is not found."""


class ConflictError(CupidClientError):
    """Raised when an operation conflicts with current circumstances."""


class ValidationError(CupidClientError):
    """Raised when provided data is not valid."""

    errors: Optional[list[ValidationProblem]]
