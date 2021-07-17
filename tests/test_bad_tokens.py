"""Tests that attempt to use tokens with various issues."""
import base64
import secrets
import unittest

from cupid import BadAuthenticationError
from cupid.testing import TestingCupid


BASE_URL = 'http://localhost:8080'


class TestBadTokens(unittest.IsolatedAsyncioTestCase):
    """Tests that attempt to use tokens with various issues."""

    async def asyncSetUp(self):
        """Create the app instance."""
        self.cupid = TestingCupid(BASE_URL)

    async def asyncTearDown(self):
        """Close the connection."""
        await self.cupid.close()

    async def assert_token_invalid(self, token: str):
        """Make sure that a token is rejected."""
        with self.assertRaises(BadAuthenticationError):
            await self.cupid.app(token)

    async def test_empty_data(self):
        """Test that a token containing only padding is rejected."""
        await self.assert_token_invalid('====')

    async def test_invalid_version(self):
        """Test that a token with an unrecognised version is rejected."""
        await self.assert_token_invalid(base64.urlsafe_b64encode(
            bytes([100, 0]) + (5).to_bytes(4, 'big') + secrets.token_bytes(),
        ).decode())

    async def test_no_secret(self):
        """Test that a token containing no secret is rejected."""
        await self.assert_token_invalid(base64.urlsafe_b64encode(
            bytes([0, 1]) + (2000).to_bytes(4, 'big'),
        ).decode())

    async def test_invalid_type(self):
        """Test that a token with an unrecognised type is rejected."""
        await self.assert_token_invalid(base64.urlsafe_b64encode(
            bytes([0, 5]) + (60).to_bytes(4, 'big') + secrets.token_bytes(),
        ).decode())
