"""Tests which fetch and manipulate individual users."""
import unittest

from cupid.testing import TestingCupid


BASE_URL = 'http://localhost:8080'


class TestUsers(unittest.IsolatedAsyncioTestCase):
    """Tests which fetch and manipulate individual users."""

    async def asyncSetUp(self):
        """Create the app instance."""
        self.cupid = TestingCupid(BASE_URL)
        await self.cupid.clear_database()
        self.app = await self.cupid.create_app('Test App')

    async def asyncTearDown(self):
        """Close the connection."""
        await self.cupid.close()
