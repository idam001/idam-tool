# -*- coding: utf-8 -*-
"""
Reconstructed original source of core/config.py
(deobfuscated from core/config.cpython-314-aarch64-linux-android.so).

Holds the runtime configuration, the Facebook endpoint registry and the
approval "gate" that locks the rest of the tool behind core.auth.
"""
import os
import sys
import random
import gc
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    TIMEOUT: float = 30.0
    RETRIES: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RATE_LIMIT_RPS: float = 5.0
    BATCH_SIZE: int = 50
    BATCH_FLUSH_INTERVAL: float = 2.0
    CONN_LIMIT: int = 100
    CONN_LIMIT_PER_HOST: int = 20
    MAX_WORKERS: int = 10
    COMPRESS_REQUESTS: bool = True
    SKIP_HEADERS: List[str] = field(default_factory=list)
    USA_ONLY: bool = False


CONFIG = Config()

ENDPOINTS = {
    'b_api': 'https://b-api.facebook.com/method/auth.login',
    'graph_v1': 'https://b-graph.facebook.com/auth/login',
    'graph_v2': 'https://graph.facebook.com/v18.0/me',
    'messenger': 'https://b-graph.facebook.com/messenger_sync_create_queue',
    'web_login': 'https://www.facebook.com/login.php',
}

ACTIVE_APIS = ['b_api', 'graph_v1', 'graph_v2']


class APIRegistry:
    """Picks a random API endpoint, weighted."""

    def __init__(self, endpoints=None, weights=None):
        self.endpoints = endpoints or ENDPOINTS
        self.weights = weights or [1] * len(self.endpoints)

    def get_random_api(self):
        total = sum(self.weights)
        cumulative = []
        c = 0
        for w in self.weights:
            c += w
            cumulative.append(c)
        r = random.uniform(0, total)
        for url, cum in zip(self.endpoints.values(), cumulative):
            if r <= cum:
                return url
        return list(self.endpoints.values())[-1]


# --- approval gate ----------------------------------------------------------
_gate_open = False


def _open_gate():
    global _gate_open
    _gate_open = True


def _make_gate():
    def _require():
        return _gate_open

    def _open():
        _open_gate()

    return _open, _require


_open, _require = _make_gate()
_require_gate = _require


def get_tool(name):
    """Return a gated callable; refuses to run before approval."""
    if not _require_gate():
        print('\n[!] Access denied. Run approval first.')
        sys.exit(1)
    return name


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
    gc.disable()
    if _monitored():
        _die(2)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)
