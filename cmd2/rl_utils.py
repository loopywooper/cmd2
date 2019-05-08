# coding=utf-8
"""
Imports the proper readline for the platform and provides utility functions for it
"""
from enum import Enum
import sys

# Prefer statically linked gnureadline if available (for macOS compatibility due to issues with libedit)
try:
    # noinspection PyPackageRequirements
    import gnureadline as readline
except ImportError:
    # Try to import readline, but allow failure for convenience in Windows unit testing
    # Note: If this actually fails, you should install readline on Linux or Mac or pyreadline on Windows
    try:
        # noinspection PyUnresolvedReferences
        import readline
    except ImportError:  # pragma: no cover
        pass


class RlType(Enum):
    """Readline library types we recognize"""
    GNU = 1
    PYREADLINE = 2
    NONE = 3


# Check what implementation of readline we are using
rl_type = RlType.NONE

# The order of this check matters since importing pyreadline will also show readline in the modules list
if 'pyreadline' in sys.modules:
    rl_type = RlType.PYREADLINE

elif 'gnureadline' in sys.modules or 'readline' in sys.modules:
    rl_type = RlType.GNU
