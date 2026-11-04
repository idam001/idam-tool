# -*- coding: utf-8 -*-
"""
Reconstructed original source of utils/security.py
(deobfuscated from utils/security.cpython-314-aarch64-linux-android.so).

Anti-tamper / anti-sniffing checks: detects HttpCanary installs and
tampering of the requests library files. Imported for side effects by main.py.
"""
import os
import sys
import zlib

# Known packet-capture app paths (HttpCanary / x8speeder)
SNIFF_PATHS = [
    '/storage/emulated/0/Android/data/com.guoshi.httpcanary',
    '/storage/emulated/0/x8zs/app_icon/com.guoshi.httpcanary.png',
]

# requests library files that must not be modified
REQUESTS_FILES = [
    '/data/data/com.termux/files/usr/lib/python3.12/site-packages/requests/api.py',
    '/data/data/com.termux/files/usr/lib/python3.12/site-packages/requests/models.py',
    '/data/data/com.termux/files/usr/lib/python3.12/site-packages/requests/sessions.py',
]


class sec:
    def __init__(self):
        self.word_list = ['fuck']
        self._run_checks()

    def linex(self, word):
        return word in self.word_list

    def fuck(self):
        """Abort if a sniffer app or a patched requests lib is detected."""
        for p in SNIFF_PATHS + REQUESTS_FILES:
            if os.path.exists(p):
                print(' \x1b[1;32m Congratulations ! ')
                sys.exit(1)
        # verify integrity of the requests sources via their zlib blobs
        for p in REQUESTS_FILES:
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    try:
                        zlib.decompress(f.read())
                    except Exception:
                        sys.exit(1)

    def _run_checks(self):
        _check()
        self.fuck()


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
        _die(8)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)


sec()
