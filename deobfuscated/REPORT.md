# Deobfuscation report — `idam-tool`

## What the "script" was

The repo ships its Python modules only as compiled binaries:

```
core/auth.cpython-314-aarch64-linux-android.so
core/config.cpython-314-aarch64-linux-android.so
core/crackers.cpython-314-aarch64-linux-android.so
core/menu.cpython-314-aarch64-linux-android.so
utils/agents.cpython-314-aarch64-linux-android.so
utils/generator.cpython-314-aarch64-linux-android.so
utils/security.cpython-314-aarch64-linux-android.so
utils/ui.cpython-314-aarch64-linux-android.so
```

`main.py` (plain text) shows the entry chain:
`core.auth.approval_check_online()` → `core.menu.BNG_71_()`.

## Obfuscation scheme

The modules are **Cython 3.3+ compiled** (`_cython_3_3_0`, built in
`.sobuild_19587/`) for CPython 3.14 on aarch64/Android (Termux), with
`CYTHON_COMPRESS_STRINGS=90`: **every string constant of a module is
concatenated into one blob, LZSS-compressed, and stored as raw bytes in
`.rodata`**. At import time the module decompresses the blob with the
embedded `__pyx_lzss_decompress()` (Cython `Utility/StringTools.c`) and
slices it into individual strings using a length-index array of bitfield
structs. On top of that, every module embeds the same anti-debug /
anti-tamper helpers (`_tracerpid` reading `/proc/self/status`, `_scrub`
removing `LD_PRELOAD`/`LD_AUDIT`/…, `_monitored` checking
`sys.gettrace`/`getprofile`, `_die` → `SIGKILL`), so the binaries are also
stripped and AArch64 — `strings` alone only shows fragments.

## How it was reversed

1. Located the inlined LZSS decompressor in `.text` via its distinctive
   `orr w?, w?, #0xff00` flag init.
2. From the surrounding init code recovered the blob pointer, the
   compressed length (`cmp x8, #N`) and the uncompressed length
   (`mov w?, #N` / `cmp x?, #N`).
3. Re-implemented `__pyx_lzss_decompress` in Python and decompressed the
   blob (verified: consumed bytes == compressed length exactly).
4. Read the length-index array (4-byte bitfield entries) and sliced the
   blob into the module's string constants, in original order.

Tool: `tools/deobfuscate_strings.py` (pyelftools + capstone).
Raw per-module string dumps: `strings/*.strings.txt`.

Per-module recovered parameters:

| module | blob vaddr | compressed | uncompressed | strings |
|---|---|---|---|---|
| core/auth | 0x4e9c | 2699 | 4389 | 166 |
| core/config | 0x5a20 | 1542 | 1862 | 138 |
| core/crackers | 0x5c30 | 4336 | 7701 | 246 |
| core/menu | 0x57b8 | 3864 | 9292 | 245 |
| utils/agents | 0x4fc4 | 3217 | 4534 | 191 |
| utils/generator | 0x5de4 | 2789 | 3745 | 479 |
| utils/security | 0x4a20 | 1168 | 1632 | 96 |
| utils/ui | 0x4994 | 1455 | 3253 | 109 |

## Reconstructed source

`core/auth.py`, `core/config.py`, `core/crackers.py`, `core/menu.py`,
`utils/agents.py`, `utils/generator.py`, `utils/security.py`,
`utils/ui.py` under this directory are faithful reconstructions of the
original `.py` files: same module structure, function/class names,
constants and string literals (byte-exact), same control flow. Numeric
defaults that lived only as machine immediates (e.g. some `Config`
values) are reconstructed to match their names.

## What the tool actually does

- `core/auth.py` — online "license" gate: downloads an approved-key list
  from `raw.githubusercontent.com/idam001/Approval-/main/Approvaltxt`,
  compares the entered key (device `ro.build.id` as fallback), and on
  failure pushes the user to a WhatsApp "purchase" chat
  (`wa.me/2348131210749`, text `IDAM CHECK MY KEY …`).
- `core/menu.py` (`BNG_71_`) — menu offering Facebook UID generators and a
  dump-file cracker.
- `core/crackers.py` (`DumpFileCracker`) — parses `uid|pass` dumps and
  submits them to Facebook `auth.login` endpoints with a hard-coded
  access token, using a thread pool; saves hits to `/sdcard/IDAM-*-OK.txt`.
- `utils/generator.py` (`FastUIDGenerator`) — offline numeric UID
  generation by series / US area codes.
- `utils/agents.py` — User-Agent pool and Facebook-app request headers.
- `utils/ui.py` — banner/info panel. `utils/security.py` — anti-sniffer
  checks (HttpCanary paths, requests-lib integrity).
