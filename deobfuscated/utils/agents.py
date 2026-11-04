# -*- coding: utf-8 -*-
"""
Reconstructed original source of utils/agents.py
(deobfuscated from utils/agents.cpython-314-aarch64-linux-android.so).

User-Agent pool + Facebook Graph API request headers.
"""
import hashlib
import os
import random
import sys

android_versions = ['10', '11', '12', '13', '14', '15.0', '16.5', '5', '5120', '5121', '5122']
ios_versions = ['15.0', '15.5', '16.0', '16.5', '17.0', '14', '13', '12', '11.0', '10.0', '1']
windows = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.',
    'Mozilla/5.0 (Windows NT 6.',
    'Mozilla/5.0 (Windows; U; Windows NT ',
]
devices = ['Pixel 6', 'Pixel 7', 'OnePlus 9 Pro', 'SM-G991B', 'SM-G998B', 'SM-N986B',
           'iPhone13,2', 'iPhone14,2', 'iPhone14,3', 'iPhone15,2']


def android_ua():
    v = random.choice(android_versions)
    d = random.choice(devices)
    return ('Mozilla/5.0 (Linux; Android ' + v + '; ' + d +
            ' Mobile/15E148 Safari/604.1')


def ios_ua():
    v = random.choice(ios_versions)
    d = random.choice([x for x in devices if x.startswith('iPhone')])
    return ('Mozilla/5.0 (iPhone; CPU iPhone OS ' + v.replace('.0', '') +
            ' like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/' +
            v + ' Mobile Safari/537.36')


def desktop_ua():
    return random.choice(windows)


ua_pool = [android_ua, ios_ua, desktop_ua]


def get_optimal_ua():
    """Return a random realistic User-Agent string."""
    return random.choice(ua_pool)()


def get_fb_api_headers():
    """Headers mimicking the official Facebook Android app (b-api calls)."""
    return {
        'User-Agent': 'Mozilla/5.0 (Linux; Android ' + random.choice(android_versions) +
                      '; ' + random.choice(devices) + ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' +
                      random.choice(['121.0.', '139.0.']) + '.0 Mobile Safari/537.36',
        'Host': 'b-graph.facebook.com',
        'content-type': 'application/x-www-form-urlencoded',
        'x-fb-connection-type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.HSPA']),
        'x-fb-connection-quality': 'EXCELLENT',
        'x-fb-connection-bandwidth': str(random.randint(5000, 9000)),
        'x-fb-http-engine': 'Liger',
        'x-fb-net-hni': str(random.randint(1000, 9999)),
        'x-fb-sim-hni': str(random.randint(1000, 9999)),
        'X-FB-Client-IP': 'true',
        'X-FB-Connection-Type': 'MOBILE.LTE',
        'X-FB-Friendly-Name': 'authenticate',
        'X-FB-HTTP-Engine': 'Liger',
        'X-FB-Request-Analytics-Tags': 'graphservice',
        'X-FB-Server-Cluster': 'true',
        'X-Tigon-Is-Retry': 'False',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }


def get_advanced_headers():
    """FB headers with per-request hashed session ids."""
    h = get_fb_api_headers()
    h['x-fb-session-id'] = hashlib.md5(str(random.random()).encode()).hexdigest()
    h['x-fb-device-group'] = hashlib.md5(os.urandom(8)).hexdigest()
    h['x-fb-connection-token'] = hashlib.md5(str(random.random()).encode()).hexdigest()
    h['nid'] = 'jiZ+yNNBgbwC;pid=Main;tid=' + str(random.randint(1000, 9999))
    h['Accept'] = ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                   'image/avif,image/webp,*/*;q=0.8')
    return h


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
        _die(4)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)
