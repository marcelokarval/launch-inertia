"""
Custom signals for identity resolution events.

These signals allow other apps to react to identity lifecycle events
(e.g., post-merge cleanup, analytics, notifications).
"""

from django.dispatch import Signal

# Fired before an identity merge is executed
# sender: Identity (source), target: Identity (target)
identity_pre_merge = Signal()

# Fired after an identity merge is completed
# sender: Identity (source), target: Identity (target), stats: dict
identity_post_merge = Signal()

# Fired when a new identity is created from resolution
# sender: Identity, source: str (e.g., "fingerprint", "form", "api")
identity_created = Signal()

# Fired when a contact is linked to an identity
# sender: Identity, contact: ContactEmail|ContactPhone, contact_type: str
identity_contact_linked = Signal()
