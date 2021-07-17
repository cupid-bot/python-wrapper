"""Tests for user sessions."""
import secrets
import unittest

from cupid import ValidationError
from cupid.testing import TestingCupid


BASE_URL = 'http://localhost:8080'


class TestSession(unittest.IsolatedAsyncioTestCase):
    """Tests for user sessions."""

    async def asyncSetUp(self):
        """Create the session instance."""
        self.cupid = TestingCupid(BASE_URL)
        await self.cupid.clear_database()
        self.access_token = secrets.token_urlsafe(256)
        self.user_id = 1245
        self.user_name = 'Artemis'
        self.user_discriminator = '0504'
        self.user_avatar_url = 'https://avatars3.githubusercontent.com/u/1245'
        await self.cupid.register_discord_token(
            token=self.access_token,
            id=self.user_id,
            name=self.user_name,
            discriminator=self.user_discriminator,
            avatar_url=self.user_avatar_url,
        )
        self.session = await self.cupid.discord_authenticate(self.access_token)

    async def asyncTearDown(self):
        """Close the connection."""
        await self.cupid.close()

    async def test_self_details(self):
        """Make sure that the user's details are correct."""
        self.assertEqual(self.session.user.id, self.user_id)
        self.assertEqual(self.session.user.name, self.user_name)
        self.assertEqual(
            self.session.user.discriminator, self.user_discriminator,
        )
        self.assertEqual(self.session.user.avatar_url, self.user_avatar_url)

    async def test_wrong_discord_token(self):
        """Make sure the server errors on an invalid Discord token."""
        token = self.access_token + '-wrong'
        with self.assertRaises(ValidationError):
            await self.cupid.discord_authenticate(token)

    async def test_use_session_token(self):
        """Test using the returned session token directly."""
        self.session = await self.cupid.user_session(self.session.token)
