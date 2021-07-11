Python API Docs
===============

.. py:module:: cupid.annotations

Cupid
-----

.. autoclass:: Cupid
   :members: base_url, __init__, app, user_session, discord_authenticate
   :undoc-members:

App
---

.. autoclass:: App
   :members: id, name, token, refresh_token, delete, get_user, graph, users, create_user
   :undoc-members:

UserSession
-----------

.. autoclass:: UserSession
   :members: id, user, expires_at, refresh_token, delete, get_user, graph, users
   :undoc-members:

User
----

.. autoclass:: User
   :members: id, name, discriminator, avatar_url, gender
   :undoc-members:

UserAsSelf
----------

.. autoclass:: UserAsSelf
   :members: id, name, discriminator, avatar_url, gender, propose, relationship, set_gender
   :undoc-members:

UserAsApp
---------

.. autoclass:: UserAsApp
   :members: id, name, discriminator, avatar_url, gender, propose, relationship, set_gender, edit
   :undoc-members:

Graph
-----

.. autoclass:: Graph
   :members: users, relationships
   :undoc-members:

UserList
--------

.. autoclass:: UserList
   :members: __len__, get_page, flatten, __aiter__
   :undoc-members:

Gender
------

.. autoclass:: Gender
   :members: NON_BINARY, FEMALE, MALE
   :undoc-members:

RelationshipKind
----------------

.. autoclass:: RelationshipKind
   :members: MARRIAGE, ADOPTION
   :undoc-members:

Relationship
------------

.. autoclass:: Relationship
   :members: id, initiator, other, kind, accepted, created_at, accepted_at
   :undoc-members:

OwnRelationship
---------------

.. autoclass:: OwnRelationship
   :members: id, initiator, other, kind, accepted, created_at, accepted_at, accept, delete
   :undoc-members:
