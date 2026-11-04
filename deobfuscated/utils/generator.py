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
