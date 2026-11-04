# -*- coding: utf-8 -*-
"""
Reconstructed original source of utils/ui.py
(deobfuscated from utils/ui.cpython-314-aarch64-linux-android.so).

Terminal banner / info panel for IDAM ULTIMATE v5.0.
"""
import os
import sys
import random

R = '\x1b[0m'
RED = '\x1b[1;31m'
GREEN = '\x1b[1;32m'
YELLOW = '\x1b[1;33m'
BLUE = '\x1b[1;34m'
MAGENTA = '\x1b[1;35m'
CYAN = '\x1b[1;36m'
WHITE = '\x1b[1;37m'
ORANGE = '\x1b[38;5;196m'
ORANGE2 = '\x1b[38;5;203m'
GREEN2 = '\x1b[38;5;40m'
BAR = '\x1b[38;5;48m' + '│' * 40

VERSION = '5.0 ULTIMATE'
OWNER = 'IDAM EMMANUEL'
GROUP_NAME = 'IDAM OLD CLONE'

____banner____ = (
    '\x1b[1;38;5;190m            \U0001f308   I D A M - U L T I M A T E  v 5 . 0   \U0001f308\x1b[0m'
    '\x1b[1;38;5;196m     \u2588\u2588\u2557\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2588\u2557    \u2588\u2588\u2588\u2557 \x1b[0m'
    '\x1b[1;38;5;202m     \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557 \u2588\u2588\u2588\u2551    \u2588\u2588\u2588\u2551   \u2588\u2588\u2588\u2551\u255a\u2550\u2588\u2588\u2557\x1b[0m'
    '\x1b[1;38;5;208m     \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2551 \u2588\u2588\u2588\u2551 \u2588\u2588\u2588\u2551    \u2588\u2588\u2588\u2551   \u2588\u2588\u2588\u2551 \u2588\u2588\u2588\u2551 \u255a\u2550\u2588\u2588\u2551\x1b[0m'
    '\x1b[1;38;5;214m     \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551 \u2588\u2588\u2588\u255a\u2550\u2588\u2588\u2557\u2588\u2588\u2551    \u2588\u2588\u2588\u2551   \u2588\u2588\u2588\u2551 \u2588\u2588\u2588\u2551 \u255a\u2550\u2588\u2588\u2551  \x1b[0m'
    '\x1b[1;38;5;220m     \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2588\u2588\u2551 \u2588\u2588\u2551\u2588\u2588\u2551 \u2588\u2588\u2588\u255a\u2550\u2588\u2557 \u2588\u2588\u2551    \u2588\u2588\u2588\u2551 \u2588\u2588\u2588\u2557\x1b[0m'
    '\x1b[1;38;5;226m     \u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u255d\u255d \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u255d     \u255a\u2550\u255d     \u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u255d \x1b[0m'
    '         IDAM ULTIMATE v5.0 \u2638\ufe0f\U0001f525'
    '\n\x1b[1;36mPremium \u2022 Fast \u2022 Secure \u2022 Professional\x1b[1;35m'
)

____info____ = (
    '\n\u2551  \U0001f465 W.S GROUP     : '
    '\n\u2551  \U0001f4ac WHATSAPP      : '
    '\n\u2551  \U0001f4a5 VERSION       : '
    '\n\u2560' + '─' * 52 + '\u2563\n'
    '\u2551                \U0001f451 ULTIMATE INFORMATION \U0001f451            \u2551\n'
    '\u255f' + '─' * 52 + '\u2563\n'
    '\u2551  \U0001f4a4 OWNER         : '
    '\n\u255f' + '─' * 52 + '\u2563\n'
    '\u2551         \u26a1 POWERED BY IDAM EMMANUEL \u26a1              \u2551\n'
    '\u255a' + '─' * 52 + '\u255d\n'
)


def clear():
    os.system('clear' if os.name != 'win' else 'cls')


def set_title():
    sys.stdout.write('\x1b]2;\U0001f9b7\u3000IDAM ULTIMATE v5.0\u3000\u2665\ufe0f\x07')
    sys.stdout.flush()


def rad(seq):
    return random.choice(seq)


def win():
    return os.name == 'win'


def show_info():
    print(____info____ + GROUP_NAME + R)


# --- shared anti-debug helpers (present in every module) --------------------
def _tracerpid():
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('TracerPid:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return '?'


def _scrub():
    for var in ('LD_PRELOAD', 'LD_AUDIT', 'LD_DEBUG', 'DEBUGGER_ID',
                'PYTHONBREAKPOINT', 'PYTHONFAULTHANDLER', 'PYTHONINSPECT',
                'PYTHONSTARTUP'):
        os.environ.pop(var, None)


def _monitored():
    if _tracerpid() not in ('0', '?'):
        return True
    if getattr(sys, 'gettrace', lambda: None)() is not None:
        return True
    if getattr(sys, 'getprofile', lambda: None)() is not None:
        return True
    return False


def _check():
    _scrub()
    if _monitored():
        _die(3)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)
