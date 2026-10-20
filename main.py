# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import uuid
import hashlib
import random
import string
import json
import urllib.parse
import asyncio
import aiohttp
import aiofiles
import signal
import gzip
import subprocess
import requests
import urllib3
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor as tred
from requests.exceptions import ConnectionError
from requests import api, models, sessions

urllib3.disable_warnings()

import utils.security

def _entry():
    from core.auth import approval_check_online
    from core.menu import BNG_71_
    approval_check_online()
    BNG_71_()

if __name__ == '__main__':
    _entry()
