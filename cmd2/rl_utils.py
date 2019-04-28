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

    from ctypes import byref
    from ctypes.wintypes import DWORD, HANDLE
    import atexit

    # Check if we are running in a terminal
    if sys.stdout.isatty():  # pragma: no cover
        # noinspection PyPep8Naming,PyUnresolvedReferences
        def enable_win_vt100(handle: HANDLE) -> bool:
            """
            Enables VT100 character sequences in a Windows console
            This only works on Windows 10 and up
            :param handle: the handle on which to enable vt100
            :return: True if vt100 characters are enabled for the handle
            """
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

            # Get the current mode for this handle in the console
            cur_mode = DWORD(0)
            readline.rl.console.GetConsoleMode(handle, byref(cur_mode))

            retVal = False

            # Check if  ENABLE_VIRTUAL_TERMINAL_PROCESSING is already enabled
            if (cur_mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING) != 0:
                retVal = True

            elif readline.rl.console.SetConsoleMode(handle, cur_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING):
                # Restore the original mode when we exit
                atexit.register(readline.rl.console.SetConsoleMode, handle, cur_mode)
                retVal = True

            return retVal

        # Enable VT100 sequences for stdout and stderr
        STD_OUT_HANDLE = -11
        STD_ERROR_HANDLE = -12
        # noinspection PyUnresolvedReferences
        vt100_stdout_support = enable_win_vt100(readline.rl.console.GetStdHandle(STD_OUT_HANDLE))
        # noinspection PyUnresolvedReferences
        vt100_stderr_support = enable_win_vt100(readline.rl.console.GetStdHandle(STD_ERROR_HANDLE))
        vt100_support = vt100_stdout_support and vt100_stderr_support

    ############################################################################################################
    # pyreadline is incomplete in terms of the Python readline API. Add the missing functions we need.
    ############################################################################################################
    # readline.redisplay()
    try:
        getattr(readline, 'redisplay')
    except AttributeError:
        # noinspection PyProtectedMember,PyUnresolvedReferences
        readline.redisplay = readline.rl.mode._update_line

    # readline.remove_history_item()
    try:
        getattr(readline, 'remove_history_item')
    except AttributeError:
        # noinspection PyProtectedMember,PyUnresolvedReferences
        def pyreadline_remove_history_item(pos: int) -> None:
            """
            An implementation of remove_history_item() for pyreadline
            :param pos: The 0-based position in history to remove
            """
            # Save of the current location of the history cursor
            saved_cursor = readline.rl.mode._history.history_cursor

            # Delete the history item
            del(readline.rl.mode._history.history[pos])

            # Update the cursor if needed
            if saved_cursor > pos:
                readline.rl.mode._history.history_cursor -= 1

        readline.remove_history_item = pyreadline_remove_history_item

elif 'gnureadline' in sys.modules or 'readline' in sys.modules:
    # We don't support libedit
    if 'libedit' not in readline.__doc__:
        rl_type = RlType.GNU

        # Load the readline lib so we can access members of it
        import ctypes
        readline_lib = ctypes.CDLL(readline.__file__)