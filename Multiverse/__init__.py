"""
Multiverse: Manage and run functions in multiple virtual environments
seamlessly.
"""

from .virtual_env_manager import VirtualEnvManager
from .decorator import universe


__all__ = ['VirtualEnvManager', 'universe']
