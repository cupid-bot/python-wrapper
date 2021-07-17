Python API Docs: Testing
========================

The API server has a testing mode, which allows a client to perform actions like wiping the database, in order to facilitate in testing it. These endpoints are implemented under the ``TestingCupid`` class, which can be used instead of ``Cupid``.

.. py:module:: cupid.testing

TestingCupid
------------

.. autoclass:: TestingCupid
   :members: base_url, __init__, testing_enabled, clear_database, create_app, app, user_session, discord_authenticate, close
