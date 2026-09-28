"""Legacy Grant / Operation Port mandates belong to the archived release.

Direct provider ACLs are supported by this event-only integration.
"""
from .model import CoordinationError

class Mandates:
    def __init__(self,*args,**kwargs):
        raise CoordinationError("UNSUPPORTED_LEGACY_MANDATE")
