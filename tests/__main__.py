"""Test runner."""
import asyncio
import pathlib
import sys
import unittest
import webbrowser

import coverage


# Add module parent dir to PATH so we can import it.
parent_path = pathlib.Path(__file__).parent.parent
sys.path.append(str(parent_path))

# Set up the coverage monitor.
cov = coverage.Coverage(source_pkgs=(
    'cupid',
), branch=True)

cov.start()
# Import after coverage measurement is started.
from cupid.testing import TestingCupid      # noqa: E402

from .test_app import TestApp               # noqa: E402, F401
from .test_bad_tokens import TestBadTokens  # noqa: E402, F401
from .test_session import TestSession       # noqa: E402, F401
from .test_users import TestUsers           # noqa: E402, F401


async def ensure_testing_mode():
    """Make sure that testing mode is enabled on the server."""
    client = TestingCupid()
    if not await client.testing_enabled():
        print('Server testing mode is not enabled.')
        sys.exit(1)
    await client.close()


asyncio.run(ensure_testing_mode())

# Run the tests.
unittest.main(exit=False)

# Fetch and display the server coverage report.


async def fetch_coverage() -> coverage.Coverage:
    """Fetch server code coverage."""
    client = TestingCupid()
    data = await client.coverage()
    await client.close()
    return data


loop = asyncio.new_event_loop()
server_coverage = loop.run_until_complete(fetch_coverage())
server_coverage.html_report(directory='server_coverage_report')
webbrowser.open(str(pathlib.Path('server_coverage_report') / 'index.html'))

# Create and display the client coverage report.
cov.stop()
cov.html_report(directory='client_coverage_report')
webbrowser.open(str(pathlib.Path('client_coverage_report') / 'index.html'))
