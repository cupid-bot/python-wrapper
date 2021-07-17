"""High-level object-orientated wrapper for the Cupid API."""
from .cupid import Cupid    # noqa: F401
from .models import *       # noqa: F401, F403


__all__ = (    # noqa: F405
    'BadAuthenticationError',
    'ConflictError',
    'Cupid',
    'CupidError',
    'CupidClientError',
    'CupidServerError',
    'ForbiddenError',
    'Gender',
    'NotFoundError',
    'RelationshipKind',
    'ValidationError',
)
