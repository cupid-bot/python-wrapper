"""Tests for the App class."""
import unittest

from cupid import BadAuthenticationError, Gender
from cupid.testing import TestingCupid


BASE_URL = 'http://localhost:8080'


class TestApp(unittest.IsolatedAsyncioTestCase):
    """Tests for the App class."""

    async def asyncSetUp(self):
        """Create the app instance."""
        self.cupid = TestingCupid(BASE_URL)
        await self.cupid.clear_database()
        self.app_name = 'Test App'
        self.app = await self.cupid.create_app(self.app_name)

    async def asyncTearDown(self):
        """Close the connection."""
        await self.cupid.close()

    async def test_fetch_app(self):
        """Make sure that the we can re-fetch the app."""
        app = await self.cupid.app(self.app.token)
        self.assertEqual(self.app.id, app.id)

    async def test_app_name(self):
        """Make sure that the app name is correct."""
        self.assertEqual(self.app.name, self.app_name)

    async def test_refresh_app_token(self):
        """Test generating a new token for the app."""
        old_token = self.app.token
        await self.app.refresh_token()
        self.assertNotEqual(old_token, self.app.token)
        # Make sure the new token works.
        await self.cupid.app(self.app.token)

    async def test_delete_app(self):
        """Test deleting the app."""
        token = self.app.token
        await self.app.delete()
        with self.assertRaises(BadAuthenticationError):
            await self.cupid.app(token)

    async def test_create_user(self):
        """Test creating a user."""
        user = await self.app.create_user(
            100,
            name="Help I'm trapped in a driver's license factory",
            discriminator=231,
            avatar_url='https://example.com/image.png',
            gender=Gender.FEMALE,
        )
        self.assertEqual(user.id, 100)
        self.assertEqual(
            user.name, "Help I'm trapped in a driver's license factory",
        )
        self.assertEqual(user.discriminator, '0231')
        self.assertEqual(user.avatar_url, 'https://example.com/image.png')
        self.assertEqual(user.gender, Gender.FEMALE)

    async def test_create_existing_user(self):
        """Test creating a user and then reusing the same ID."""
        await self.app.create_user(
            212644551326411969,
            name="Robert'); DROP TABLE Students;--",
            discriminator='1211',
            avatar_url='http://example.com/path/to/image.jpg',
            gender='non_binary',
        )
        user = await self.app.create_user(
            212644551326411969,
            name='Little Bobby Tables',
            discriminator='0005',
            avatar_url='https://example.org/fancy-image.webp',
            gender='male',
        )
        self.assertEqual(user.id, 212644551326411969)
        self.assertEqual(user.name, 'Little Bobby Tables')
        self.assertEqual(user.discriminator, '0005')
        self.assertEqual(
            user.avatar_url, 'https://example.org/fancy-image.webp',
        )
        self.assertEqual(user.gender, Gender.MALE)
