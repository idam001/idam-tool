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
