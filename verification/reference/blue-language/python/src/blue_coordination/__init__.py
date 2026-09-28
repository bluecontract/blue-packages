"""Automatic Coordination; Runner is the explicit predecessor integration."""
from .runner import Runner, SignedTimelines, required_sources
from blue_coordination_spec import (Coordinator,Catalogue as SpecificationCatalogue,
    LocalProvider,ProviderSet,PrefixVerifier,Store,CoordinationError as SpecificationError)
from .engine import CoordinationEngine, SourceHub, MemoryStore, SQLiteStore
LegacyRunner = Runner
__version__='1.0.0.dev4'
__all__=['Runner','SignedTimelines','required_sources','Coordinator','SpecificationCatalogue',
         'LocalProvider','ProviderSet','PrefixVerifier','Store','SpecificationError',
         'CoordinationEngine','SourceHub','MemoryStore','SQLiteStore','LegacyRunner']
