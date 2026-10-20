#!/usr/bin/env python3
# file: encrypt.py
# @ YounisXyz — MAX v4.8

import os, sys, shutil, random, string, base64, lzma, marshal, struct, time
import subprocess, sysconfig, platform

# ==================== TOGGLES ===============================
T_SELF_INTEGRITY   = True
T_HW_BREAKPOINT    = True
T_TRAP_FLAG        = True
T_RANDOM_KEY       = True
T_SECTION_RENAME   = True
T_DECOY_SECTIONS   = True
T_FORK_WATCHDOG    = True
T_PTHREAD_WATCHDOG = True
T_STATIC_LIBPYTHON = True
T_STRIP_SECTIONS   = True
T_SSTRIP           = True
T_UPX              = False
T_KILL_STALE       = True
T_SO_HARDEN        = True
OUTPUT_DIR         = None
STORAGE_CANDIDATES = [
    "/sdcard/Download", "/sdcard",
    "/storage/emulated/0/Download", "/storage/emulated/0",
    os.path.expanduser("~/storage/downloads"),
    os.path.expanduser("~/storage/shared"),
]
# ============================================================

reset = "\x1b[0m"; green = "\x1b[1;32m"; yellow = "\x1b[1;33m"
red = "\x1b[1;91m"; cyan = "\x1b[1;36m"; purple = "\x1b[1;35m"

_STAGE_TOTAL = 12
_STAGE_N = 0
_T0 = 0.0

def _stage_reset():
    global _STAGE_N, _T0
    _STAGE_N = 0; _T0 = time.time()

def _stage(label, ok=True):
    global _STAGE_N
    _STAGE_N += 1
    mark = green + "OK " + reset if ok else red + "FAIL " + reset
    tag  = f"{cyan}[{_STAGE_N:>2}/{_STAGE_TOTAL}]{reset}"
    print(f"  {tag} {mark}{label}")

def _stage_done():
    dt = time.time() - _T0
    print(f"\n  {purple}── done in {dt:.2f}s ──{reset}")

def _clear(): os.system("cls" if os.name == "nt" else "clear")

def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)

def _rand_names(n):
    used, out = set(), []
    while len(out) < n:
        name = "_" + "".join(random.choices(string.ascii_lowercase, k=6))
        if name not in used:
            used.add(name); out.append(name)
    return out

def _arch():
    m = platform.machine().lower()
    if m in ("x86_64", "amd64"):  return "x86_64"
    if m in ("aarch64", "arm64"): return "aarch64"
    if m.startswith("arm"):       return "arm"
    return m

def _rand_section_name(prefix):
    return f"{prefix}.{''.join(random.choices(string.ascii_lowercase, k=8))}"

def _pick_output_dir():
    if OUTPUT_DIR:
        os.makedirs(OUTPUT_DIR, exist_ok=True); return OUTPUT_DIR
    for c in STORAGE_CANDIDATES:
        try:
            if os.path.isdir(c) and os.access(c, os.W_OK): return c
        except Exception: continue
    return os.getcwd()

def _which_cython():
    py = sys.executable
    out = []
    if shutil.which("cython"):   out.append(["cython"])
    out.append([py, "-m", "cython"])
    if shutil.which("cython3"):  out.append(["cython3"])
    return out

def _which_cythonize():
    py = sys.executable
    out = []
    if shutil.which("cythonize"):   out.append(["cythonize"])
    out.append([py, "-m", "cythonize"])
    return out

# ---------------- safe deploy ----------------
def _kill_stale(dest):
    if not T_KILL_STALE: return
    name = os.path.basename(dest)
    _run(["pkill", "-9", "-f", dest])
    if shutil.which("killall"):
        _run(["killall", "-9", name])
    else:
        try:
            for pid in os.listdir("/proc"):
                if not pid.isdigit(): continue
                try:
                    with open(f"/proc/{pid}/comm") as f:
                        comm = f.read().strip()
                    if comm == name[:15]:
                        os.kill(int(pid), 9)
                except Exception:
                    continue
        except Exception:
            pass
    time.sleep(0.3)

def _safe_deploy(src, dest):
    abs_src = os.path.abspath(src)
    abs_dest = os.path.abspath(dest)
    if abs_src == abs_dest:
        return True, "in place"
    _kill_stale(abs_dest)
    tmp = abs_dest + ".new"
    try:
        shutil.copy2(abs_src, tmp)
        try: os.chmod(tmp, 0o755)
        except Exception: pass
        os.replace(tmp, abs_dest)
        return True, abs_dest
    except Exception as e:
        try: os.remove(tmp)
        except Exception: pass
        return False, str(e)

def Banner():
    _clear()
    return (
        reset + "\n"
        + "   8888888888 888b    888  .d8888b.  \n"
        + "   888        8888b   888 d88P  Y88b \n"
        + "   888        88888b  888 888    888 \n"
        + "   8888888    888Y88b 888 888        \n"
        + "   888        888 Y88b888 888        \n"
        + "   888        888  Y88888 888    888 \n"
        + "   888        888   Y8888 Y88b  d88P \n"
        + "   8888888888 888    Y888  \"Y8888P\"\n\n"
        + reset
        + "----------------------------------------------\n"
        + "Author    :   Muhammad Younis (MAX v4.8)\n"
        + "WhatsApp  :   +923194999455\n"
        + "Github    :   https://github.com/YounisXyz\n"
        + "----------------------------------------------"
    )

# ---------------- python-level anti-debug ----------------
ANTIDEBUG_PY = r'''
import sys as _s, os as _o, ctypes as _c

def _die(code=1):
    try: _o._exit(code)
    except Exception: _s.exit(code)

def _tracerpid():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("TracerPid:"):
                    return int(line.split(":")[1].strip())
    except Exception: pass
    return 0

def _monitored():
    m = getattr(_s, "monitoring", None)
    if m is None: return False
    try: return m.get_tool(m.DEBUGGER_ID) is not None
    except Exception: return False

def _scrub():
    for v in ("PYTHONINSPECT","PYTHONBREAKPOINT","PYTHONFAULTHANDLER",
              "PYTHONSTARTUP","LD_PRELOAD","LD_AUDIT","LD_DEBUG"):
        _o.environ.pop(v, None)

def _check():
    if _s.gettrace() is not None:   _die()
    if _s.getprofile() is not None: _die()
    if _monitored():                _die()
    if _tracerpid() != 0:           _die()
    if _o.environ.get("PYTHONINSPECT"):    _die()
    if _o.environ.get("PYTHONBREAKPOINT"): _die()

_scrub(); _check()
'''

def inject_anti_debug_py(src, dst):
    with open(src, "r", encoding="utf-8", errors="replace") as f:
        body = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(ANTIDEBUG_PY + "\n\n" + body)

# ---------------- native .so stub ----------------
_SO_STUB = r'''/* _adstub_so.c — constructor anti-debug for Cython .so */
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/prctl.h>
#include <sys/mman.h>
#include <sys/ptrace.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/user.h>
#include <time.h>

#if defined(__x86_64__) || defined(__i386__)
  #include <x86intrin.h>
  #define _AD_TS()  __rdtsc()
#elif defined(__aarch64__) || defined(__arm__)
  static inline unsigned long long _ad_ts(void) {
      unsigned long long v; __asm__ __volatile__("mrs %0, cntvct_el0" : "=r"(v)); return v;
  }
  #define _AD_TS()  _ad_ts()
#else
  #define _AD_TS()  0ULL
#endif

static const unsigned char _AD_K = 0x__KK__;
static int _ad_stage = 0;

__attribute__((noinline))
static void _ad_deobf(char *dst, const unsigned char *enc, int n) {
    for (int i = 0; i < n; i++) dst[i] = (char)(enc[i] ^ _AD_K);
}

static void _ad_die(void) {
    if (getenv("AD_DEBUG")) {
        char b[48];
        int n = snprintf(b, sizeof b, "[AD-SO] killed at stage %d\n", _ad_stage);
        if (n > 0) write(2, b, (size_t)n);
    }
    syscall(SYS_kill, getpid(), SIGKILL);
    _exit(127);
}

static int _ad_tracerpid(void) {
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return 0;
    char line[256]; int pid = 0;
    while (fgets(line, sizeof line, f)) {
        if (!strncmp(line, "TracerPid:", 10)) { pid = atoi(line + 10); break; }
    }
    fclose(f);
    return pid;
}

static int _ad_dumpable(void) {
    errno = 0;
    int r = prctl(PR_GET_DUMPABLE, 0, 0, 0, 0);
    return (errno == 0) ? r : -1;
}

#if defined(__x86_64__)
static int _ad_hw_bp(void) {
    struct user_regs_struct r;
    errno = 0;
    if (ptrace(PTRACE_GETREGS, getpid(), 0, &r) != 0) return 0;
    return (r.dr0 | r.dr1 | r.dr2 | r.dr3) != 0;
}
#endif

#if defined(__x86_64__) || defined(__i386__)
static int _ad_trap_flag(void) {
    unsigned long long flags = 0;
    __asm__ __volatile__("pushfq; popq %0" : "=r"(flags));
    return (flags >> 8) & 1u;
}
static int _ad_hv_bit(void) {
    unsigned int a, b, c, d;
    __asm__ __volatile__("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(1));
    return (int)((c >> 31) & 1u);
}
#endif

static int _ad_scan_maps(void) {
    static const unsigned char n_gdb[]  = { __N_GDB__ };
    static const unsigned char n_lldb[] = { __N_LLDB__ };
    static const unsigned char n_fri[]  = { __N_FRIDA__ };
    static const unsigned char n_mag[]  = { __N_MAGISK__ };
    const unsigned char *nds[] = { n_gdb, n_lldb, n_fri, n_mag };
    const int lens[] = { sizeof(n_gdb), sizeof(n_lldb), sizeof(n_fri), sizeof(n_mag) };

    FILE *f = fopen("/proc/self/maps", "r");
    if (!f) return 0;
    char line[1024], buf[64];
    int hit = 0;
    while (fgets(line, sizeof line, f)) {
        for (int i = 0; i < 4; i++) {
            int L = lens[i]; if (L > 63) L = 63;
            _ad_deobf(buf, nds[i], L - 1);
            buf[L - 1] = 0;
            if (strstr(line, buf)) { hit = 1; break; }
        }
        if (hit) break;
    }
    fclose(f);
    return hit;
}

__attribute__((constructor(101)))
static void _ad_so_init(void) {
    _ad_stage = 1;
    prctl(PR_SET_DUMPABLE, 0, 0, 0, 0);
    prctl(PR_SET_NAME, (unsigned long)0x5f41444d, 0, 0, 0);
    signal(SIGTRAP, SIG_IGN);
    signal(SIGCONT, SIG_IGN);

    _ad_stage = 2;
    if (_ad_dumpable() != 0) _ad_die();

    _ad_stage = 4;
    if (_ad_tracerpid() != 0) _ad_die();

#if defined(__x86_64__) || defined(__i386__)
    _ad_stage = 5;
    if (_ad_trap_flag()) _ad_die();
    _ad_stage = 6;
    if (_ad_hv_bit()) _ad_die();
  #if defined(__x86_64__)
    _ad_stage = 7;
    if (_ad_hw_bp()) _ad_die();
  #endif
#endif

    _ad_stage = 30;
    if (_ad_scan_maps()) _ad_die();

    _ad_stage = 33;
    {
        unsigned long long t1 = _AD_TS();
        volatile unsigned long long s = 0;
        for (int i = 0; i < 4000; i++) s += (unsigned)(i * 2654435761u);
        (void)s;
        unsigned long long t2 = _AD_TS();
        if (t2 > t1 && (t2 - t1) > 200000000ULL) _ad_die();
    }

    unsetenv("LD_PRELOAD"); unsetenv("LD_AUDIT"); unsetenv("LD_DEBUG");
    unsetenv("PYTHONINSPECT"); unsetenv("PYTHONBREAKPOINT");
    unsetenv("PYTHONSTARTUP"); unsetenv("PYTHONFAULTHANDLER");

    _ad_stage = 0;
}
'''

def build_so_stub_c():
    key = random.randint(1, 255) if T_RANDOM_KEY else 0x5A
    while key == 0: key = random.randint(1, 255)
    def _xe(text):
        return ", ".join(f"0x{b ^ key:02x}" for b in (text.encode("ascii") + b"\x00"))
    out = _SO_STUB
    out = out.replace("__KK__",      f"{key:02X}")
    out = out.replace("__N_GDB__",   _xe("gdb"))
    out = out.replace("__N_LLDB__",  _xe("lldb"))
    out = out.replace("__N_FRIDA__", _xe("frida"))
    out = out.replace("__N_MAGISK__",_xe("magisk"))
    return out, key

# ---------------- native ELF stub ----------------
_ADSTUB = r'''/* _adstub.h — MAX v4.8 */
#ifndef _ADSTUB_H
#define _ADSTUB_H 1

#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/prctl.h>
#include <sys/mman.h>
#include <sys/ptrace.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <time.h>

#if defined(__x86_64__) || defined(__i386__)
  #include <x86intrin.h>
  #define _AD_TS()  __rdtsc()
#elif defined(__aarch64__) || defined(__arm__)
  static inline unsigned long long _ad_ts(void) {
      unsigned long long v; __asm__ __volatile__("mrs %0, cntvct_el0" : "=r"(v)); return v;
  }
  #define _AD_TS()  _ad_ts()
#else
  #define _AD_TS()  0ULL
#endif

static const unsigned char _AD_K = 0x__KK__;

#define _AD_MAGIC 0x414d455441444142ULL

struct _ad_meta_s { uint64_t magic, off, sz, hash; };
__attribute__((section(".admeta"), used, aligned(16)))
static volatile struct _ad_meta_s _ad_meta = { _AD_MAGIC, 0, 0, 0 };

__attribute__((section(".adenc"), used, aligned(64)))
static const unsigned char _adenc_blob[] = {
__NEEDLES__
};
static const int _adenc_len = (int)sizeof(_adenc_blob);

__attribute__((used)) static const char _dc1[] = "UPX!";
__attribute__((used)) static const char _dc2[] = "GCC: (GNU) 11.2.0";
__attribute__((used)) static const char _dc3[] = "Py_Initialize";

static int _ad_stage = 0;

__attribute__((noinline))
static void _ad_deobf(char *dst, const unsigned char *enc, int n) {
    for (int i = 0; i < n; i++) dst[i] = (char)(enc[i] ^ _AD_K);
}

static void _ad_die(void) {
    if (getenv("AD_DEBUG")) {
        char b[48];
        int n = snprintf(b, sizeof b, "[AD] killed at stage %d\n", _ad_stage);
        if (n > 0) write(2, b, (size_t)n);
    }
    syscall(SYS_kill, getpid(), SIGKILL);
    _exit(127);
}

static int _ad_tracerpid(void) {
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return 0;
    char line[256]; int pid = 0;
    while (fgets(line, sizeof line, f)) {
        if (!strncmp(line, "TracerPid:", 10)) { pid = atoi(line + 10); break; }
    }
    fclose(f);
    return pid;
}

static int _ad_dumpable(void) {
    errno = 0;
    int r = prctl(PR_GET_DUMPABLE, 0, 0, 0, 0);
    return (errno == 0) ? r : -1;
}

static int _ad_self_integrity(void) {
    _ad_stage = 20;
    if (_ad_meta.magic != _AD_MAGIC) return 0;
    _ad_stage = 21;
    if (_ad_meta.off == 0 || _ad_meta.sz == 0 || _ad_meta.hash == 0) return 0;
    _ad_stage = 22;
    int fd = open("/proc/self/exe", O_RDONLY);
    if (fd < 0) return 0;
    _ad_stage = 23;
    if (lseek(fd, (off_t)_ad_meta.off, SEEK_SET) != (off_t)_ad_meta.off) {
        close(fd); return 0;
    }
    _ad_stage = 24;
    unsigned char buf[4096];
    size_t remain = (size_t)_ad_meta.sz;
    uint64_t h = 1469598103934665603ULL;
    while (remain) {
        size_t chunk = remain > sizeof buf ? sizeof buf : remain;
        ssize_t r = read(fd, buf, chunk);
        if (r <= 0) { close(fd); return 0; }
        for (ssize_t i = 0; i < r; i++) { h ^= buf[i]; h *= 1099511628211ULL; }
        remain -= (size_t)r;
    }
    close(fd);
    _ad_stage = 25;
    return (h == (uint64_t)_ad_meta.hash) ? 0 : 1;
}

#if defined(__x86_64__)
static int _ad_hw_bp(void) {
    struct user_regs_struct r;
    errno = 0;
    if (ptrace(PTRACE_GETREGS, getpid(), 0, &r) != 0) return 0;
    return (r.dr0 | r.dr1 | r.dr2 | r.dr3) != 0;
}
#endif

#if defined(__x86_64__) || defined(__i386__)
static int _ad_trap_flag(void) {
    unsigned long long flags = 0;
    __asm__ __volatile__("pushfq; popq %0" : "=r"(flags));
    return (flags >> 8) & 1u;
}
static int _ad_hv_bit(void) {
    unsigned int a, b, c, d;
    __asm__ __volatile__("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(1));
    return (int)((c >> 31) & 1u);
}
#endif

static int _ad_scan(const char *path, const unsigned char **nds, const int *lens, int n) {
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    char line[1024], buf[128];
    int hit = 0;
    while (fgets(line, sizeof line, f)) {
        for (int i = 0; i < n; i++) {
            int L = lens[i]; if (L > 127) L = 127;
            _ad_deobf(buf, nds[i], L - 1);
            buf[L - 1] = 0;
            if (strstr(line, buf)) { hit = 1; break; }
        }
        if (hit) break;
    }
    fclose(f);
    return hit;
}

static int _ad_scan_adenc(void) {
    char decoded[512];
    int n = _adenc_len < (int)sizeof(decoded) - 1 ? _adenc_len : (int)sizeof(decoded) - 1;
    _ad_deobf(decoded, _adenc_blob, n);
    decoded[n] = 0;
    FILE *f = fopen("/proc/self/maps", "r");
    if (!f) { memset(decoded, 0, sizeof decoded); return 0; }
    char line[1024];
    int hit = 0;
    while (fgets(line, sizeof line, f)) {
        char *p = decoded;
        while (*p && !hit) {
            if (strstr(line, p)) { hit = 1; break; }
            p += strlen(p) + 1;
        }
        if (hit) break;
    }
    fclose(f);
    memset(decoded, 0, sizeof decoded);
    return hit;
}

static volatile int _ad_stop = 0;

static void *_ad_watchdog(void *a) {
    (void)a;
    prctl(PR_SET_NAME, (unsigned long)0x6b776f72, 0, 0, 0);
    while (!_ad_stop) {
        _ad_stage = 40;
        if (_ad_tracerpid() != 0) _ad_die();
        _ad_stage = 41;
        if (_ad_dumpable() != 0) _ad_die();
        _ad_stage = 42;
        if (_ad_scan_adenc()) _ad_die();
        struct timespec ts = {0, 250000000L};
        nanosleep(&ts, NULL);
    }
    return NULL;
}

static void _ad_spawn_watchdog(void) {
    pthread_t t; pthread_attr_t a;
    pthread_attr_init(&a);
    pthread_attr_setdetachstate(&a, PTHREAD_CREATE_DETACHED);
    if (pthread_create(&t, &a, _ad_watchdog, NULL) != 0) _ad_die();
    pthread_attr_destroy(&a);
}

static void _ad_fork_watchdog(void) {
    pid_t parent = getpid();
    pid_t w = fork();
    if (w < 0) return;
    if (w > 0) return;
    prctl(PR_SET_NAME, (unsigned long)0x6b776f72, 0, 0, 0);
    pid_t orig = getppid();
    char path[64];
    snprintf(path, sizeof path, "/proc/%d/status", (int)parent);
    for (;;) {
        if (getppid() != orig) _exit(0);
        if (kill(parent, 0) != 0) _exit(0);
        FILE *f = fopen(path, "r");
        if (!f) _exit(0);
        char line[256]; int tp = 0;
        while (fgets(line, sizeof line, f)) {
            if (!strncmp(line, "TracerPid:", 10)) { tp = atoi(line + 10); break; }
        }
        fclose(f);
        if (tp != 0) { kill(parent, SIGKILL); _exit(0); }
        struct timespec ts = {0, 150000000L};
        nanosleep(&ts, NULL);
    }
}

__attribute__((constructor(101)))
static void _ad_init(void) {
    _ad_stage = 1;
    prctl(PR_SET_DUMPABLE, 0, 0, 0, 0);
    prctl(PR_SET_NAME, (unsigned long)0x5f41444d, 0, 0, 0);
    signal(SIGTRAP, SIG_IGN);
    signal(SIGCONT, SIG_IGN);

    _ad_stage = 2;
    if (_ad_dumpable() != 0) _ad_die();
    _ad_stage = 4;
    if (_ad_tracerpid() != 0) _ad_die();

#if defined(__x86_64__) || defined(__i386__)
    _ad_stage = 5;
    if (_ad_trap_flag()) _ad_die();
    _ad_stage = 6;
    if (_ad_hv_bit()) _ad_die();
  #if defined(__x86_64__)
    _ad_stage = 7;
    if (_ad_hw_bp()) _ad_die();
  #endif
#endif

    if (__SELF_INTEGRITY__) {
        _ad_stage = 8;
        int r = _ad_self_integrity();
        if (r == 1) _ad_die();
    }

    _ad_stage = 30;
    {
        volatile char t1[6] = {0x66,0x72,0x69,0x64,0x61,0x00};
        volatile char t2[4] = {0x67,0x64,0x62,0x00};
        char n1[8], n2[8];
        for (int i=0;i<6;i++) n1[i]=t1[i]; n1[6]=0;
        for (int i=0;i<4;i++) n2[i]=t2[i]; n2[4]=0;
        FILE *f = fopen("/proc/self/maps", "r");
        if (f) {
            char line[1024];
            while (fgets(line, sizeof line, f)) {
                if (strstr(line, n1) || strstr(line, n2)) { fclose(f); _ad_die(); }
            }
            fclose(f);
        }
        memset(n1,0,sizeof n1); memset(n2,0,sizeof n2);
    }

    _ad_stage = 31;
    if (_ad_scan_adenc()) _ad_die();

    _ad_stage = 32;
    {
        static const unsigned char v0[] = { __NEEDLE_VMWARE__ };
        static const unsigned char v1[] = { __NEEDLE_VBOX__ };
        static const unsigned char v2[] = { __NEEDLE_QEMU__ };
        static const unsigned char v3[] = { __NEEDLE_KVM__ };
        static const unsigned char v4[] = { __NEEDLE_HYPERV__ };
        const unsigned char *nds[] = { v0,v1,v2,v3,v4 };
        const int lens[] = { sizeof(v0),sizeof(v1),sizeof(v2),sizeof(v3),sizeof(v4) };
        if (_ad_scan("/sys/class/dmi/id/product_name", nds, lens, 5)) _ad_die();
        if (_ad_scan("/sys/class/dmi/id/sys_vendor",   nds, lens, 5)) _ad_die();
        if (_ad_scan("/sys/class/dmi/id/board_vendor", nds, lens, 5)) _ad_die();
    }

    _ad_stage = 33;
    {
        unsigned long long t1 = _AD_TS();
        volatile unsigned long long s = 0;
        for (int i = 0; i < 6000; i++) s += (unsigned)(i * 2654435761u);
        (void)s;
        unsigned long long t2 = _AD_TS();
        if (t2 > t1 && (t2 - t1) > 200000000ULL) _ad_die();
    }

#ifdef MADV_DONTDUMP
    _ad_stage = 34;
    {
        void *p = mmap(NULL, 1<<20, PROT_READ|PROT_WRITE,
                       MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
        if (p != MAP_FAILED) { madvise(p, 1<<20, MADV_DONTDUMP); munmap(p, 1<<20); }
    }
#endif

    unsetenv("LD_PRELOAD");  unsetenv("LD_AUDIT");  unsetenv("LD_DEBUG");
    unsetenv("PYTHONINSPECT"); unsetenv("PYTHONBREAKPOINT");
    unsetenv("PYTHONSTARTUP"); unsetenv("PYTHONFAULTHANDLER");

    _ad_stage = 35;
    if (__FORK_WD__)    _ad_fork_watchdog();
    if (__PTHREAD_WD__) _ad_spawn_watchdog();
    _ad_stage = 0;
}

#endif
'''

def _needles_xor_block(key, needles):
    blob = b""
    for n in needles:
        blob += n.encode("ascii") + b"\x00"
    if len(blob) % 64: blob += b"\x00" * (64 - len(blob) % 64)
    return bytes(b ^ key for b in blob), len(blob)

def build_adstub_c():
    key = random.randint(1, 255) if T_RANDOM_KEY else 0x5A
    while key == 0: key = random.randint(1, 255)
    def _xe(text):
        return ", ".join(f"0x{b ^ key:02x}" for b in (text.encode("ascii") + b"\x00"))
    needles = ["gdb", "lldb", "frida", "xposed", "magisk",
               "substrate", "gdbstub", "debugserver"]
    enc_blob, _ = _needles_xor_block(key, needles)
    blob_lines = []
    for i in range(0, len(enc_blob), 16):
        blob_lines.append("    " + ", ".join(f"0x{b:02x}" for b in enc_blob[i:i+16]) + ",")
    out = _ADSTUB
    out = out.replace("__KK__",  f"{key:02X}")
    out = out.replace("__NEEDLES__", "\n".join(blob_lines))
    out = out.replace("__NEEDLE_VMWARE__",  _xe("vmware"))
    out = out.replace("__NEEDLE_VBOX__",    _xe("vbox"))
    out = out.replace("__NEEDLE_QEMU__",    _xe("qemu"))
    out = out.replace("__NEEDLE_KVM__",     _xe("kvm"))
    out = out.replace("__NEEDLE_HYPERV__",  _xe("microsoft corporation virtual"))
    out = out.replace("__SELF_INTEGRITY__", "1" if T_SELF_INTEGRITY else "0")
    out = out.replace("__FORK_WD__",        "1" if T_FORK_WATCHDOG else "0")
    out = out.replace("__PTHREAD_WD__",     "1" if T_PTHREAD_WATCHDOG else "0")
    return out, key

def _cflags():
    a = _arch()
    flags = [
        "-O2", "-flto", "-fvisibility=hidden", "-fno-plt",
        "-fno-asynchronous-unwind-tables", "-fno-unwind-tables",
        "-fstack-protector-strong",
        "-ffunction-sections", "-fdata-sections",
        "-fno-ident", "-fno-semantic-interposition",
        "-fno-builtin", "-fno-common", "-fno-jump-tables",
    ]
    if a == "x86_64":
        flags += ["-fcf-protection=full", "-mshstk"]
    return flags

def _ldflags():
    a = _arch()
    flags = [
        "-Wl,-z,relro,-z,now", "-Wl,-z,noexecstack",
        "-Wl,-z,separate-code", "-Wl,-z,nodlopen",
        "-Wl,--build-id=none", "-Wl,--gc-sections",
        "-Wl,--as-needed", "-Wl,-Bsymbolic", "-Wl,-s",
    ]
    if a == "x86_64":
        flags += ["-Wl,-z,ibtplt", "-Wl,-z,shstk"]
    return flags

def _so_cflags():
    a = _arch()
    flags = [
        "-O2", "-fPIC", "-shared",
        "-fvisibility=hidden",
        "-fno-plt",
        "-fno-asynchronous-unwind-tables", "-fno-unwind-tables",
        "-fstack-protector-strong",
        "-ffunction-sections", "-fdata-sections",
        "-fno-ident", "-fno-semantic-interposition",
        "-fno-common", "-fno-jump-tables",
    ]
    if a == "x86_64":
        flags += ["-fcf-protection=full"]
    return flags

def _so_ldflags():
    return [
        "-Wl,-z,relro,-z,now", "-Wl,-z,noexecstack",
        "-Wl,-z,separate-code", "-Wl,--gc-sections",
        "-Wl,--as-needed", "-Wl,-Bsymbolic", "-Wl,-s",
    ]

def _find_static_libpython():
    if not T_STATIC_LIBPYTHON: return None
    ver = sysconfig.get_config_var("VERSION")
    if not ver: return None
    libdir = sysconfig.get_config_var("LIBDIR") or ""
    cands = []
    if libdir:
        cands += [os.path.join(libdir, f"libpython{ver}.a"),
                  os.path.join(libdir, f"libpython{ver}m.a")]
    for d in ("/usr/lib", "/usr/local/lib",
              "/usr/lib/x86_64-linux-gnu", "/usr/lib/aarch64-linux-gnu"):
        cands.append(os.path.join(d, f"libpython{ver}.a"))
    for c in cands:
        if os.path.isfile(c): return c
    return None

# ---------------- 1: marshal ----------------
def Marshal():
    global _STAGE_TOTAL
    _STAGE_TOTAL = 6
    _stage_reset()
    print(reset + "\nFor Example: " + green + "/sdcard/filename.py" + reset)
    src = input("Enter Your File Name :" + green + " ").strip()
    if not os.path.isfile(src):
        print(red + "File Not Found!"); return
    _stage("source located")
    with open(src, "rb") as f: raw_src = f.read()
    code = compile(raw_src, "<anon>", "exec"); _stage("compiled")
    raw  = marshal.dumps(code); _stage("marshal.dumps")
    comp = lzma.compress(raw, preset=9 | lzma.PRESET_EXTREME)
    _stage(f"lzma ({len(comp)} B)")
    key   = os.urandom(16)
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(comp))
    b85   = base64.b85encode(xored).decode("ascii")
    chunks = [b85[i:i + 96] for i in range(0, len(b85), 96)]
    _stage(f"xor+b85 ({len(b85)} ch)")
    out = input(reset + green + "Save As (e.g., encrypted.py" + reset).strip()
    if not out.endswith(".py"): out += ".py"
    out_dir = _pick_output_dir()
    final_out = out if os.path.isabs(out) else os.path.join(out_dir, os.path.basename(out))
    lz, b64, msh, ky, pl, dc, xr = _rand_names(7)
    lines = [
        "# @ YounisXyz",
        f"import lzma as {lz}, base64 as {b64}, marshal as {msh}",
        f"{ky} = bytes.fromhex('{key.hex()}')",
        f"{pl} = [",
    ]
    for c in chunks: lines.append(f"    '{c}',")
    lines += [
        "]",
        f"{dc} = {b64}.b85decode(''.join({pl}))",
        f"{xr} = bytes(_b ^ {ky}[i % len({ky})] for i, _b in enumerate({dc}))",
        f"exec({msh}.loads({lz}.decompress({xr})))",
    ]
    tmp = final_out + ".new"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    try: os.replace(tmp, final_out)
    except Exception as e:
        print(red + f"deploy failed: {e}"); return
    _stage("written (atomic)")
    _stage_done()
    print(green + f"\n  → {final_out}")

# ---------------- 2: cython .so — fixed module name ----------------
def Cythonize():
    global _STAGE_TOTAL
    _STAGE_TOTAL = 10
    _stage_reset()

    print(reset + "\nFor Example: " + green + "/sdcard/filename.py" + reset)
    src = input("Put File Location :" + green + " ").strip()
    if not os.path.isfile(src):
        print(red + "File Not Found"); return
    _stage("source located")

    # module name = how you will `import` it. cython derives PyInit_<name> from
    # the source filename, so the temp .py must be named <mod_name>.py — not
    # an obfuscated name — or the .so's export won't match its filename.
    mod_name = input(reset + green + "Module name to import as (e.g., approval): " + reset).strip()
    if not mod_name:
        mod_name = os.path.splitext(os.path.basename(src))[0]
    # strip anything that isn't a valid python identifier
    mod_name = "".join(c if (c.isalnum() or c == "_") else "_" for c in mod_name)
    if not mod_name or mod_name[0].isdigit():
        mod_name = "m_" + mod_name

    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    target_so  = mod_name + ext_suffix

    # build in a scratch dir so <mod_name>.py can't clobber a real file
    scratch = f".sobuild_{os.getpid()}"
    os.makedirs(scratch, exist_ok=True)
    temp_py = os.path.join(scratch, mod_name + ".py")
    inject_anti_debug_py(src, temp_py)
    _stage(f"py anti-debug injected (module: {mod_name})")

    # cython → .c
    c_out = os.path.join(scratch, mod_name + ".c")
    ok, last = False, ""
    for pre in _which_cython():
        cmd = pre + ["-3", "-X", "language_level=3",
                     "-X", "embedsignature=False",
                     "--no-docstrings",
                     "-o", c_out, temp_py]
        rc, so, se = _run(cmd)
        if rc == 0 and os.path.exists(c_out):
            ok = True; break
        last = se or so
    if not ok:
        print(red + "cython failed:\n" + last)
        shutil.rmtree(scratch, ignore_errors=True)
        return
    _stage(f"cython translated → {mod_name}.c")

    if T_SO_HARDEN:
        stub_c = os.path.join(scratch, "_adstub_so.c")
        with open(stub_c, "w") as f:
            f.write(build_so_stub_c()[0])
        _stage("native .so anti-debug written")

    cc = shutil.which("cc") or shutil.which("gcc")
    if not cc:
        print(red + "no C compiler")
        shutil.rmtree(scratch, ignore_errors=True)
        return

    inc = sysconfig.get_path("include")
    ver = sysconfig.get_config_var("VERSION")

    so_out = os.path.join(scratch, target_so)

    if T_SO_HARDEN:
        cmd = [cc] + _so_cflags() + [
            c_out, stub_c,
            "-o", so_out,
            f"-I{inc}", f"-lpython{ver}", "-lm", "-lpthread",
        ] + _so_ldflags()
    else:
        cmd = [cc, "-shared", "-fPIC", "-O2",
               c_out, "-o", so_out,
               f"-I{inc}", f"-lpython{ver}", "-lm", "-lpthread"]

    rc, so, se = _run(cmd)
    if rc != 0 and T_SO_HARDEN:
        _stage("hardened .so compile failed, fallback", ok=False)
        cmd = [cc, "-shared", "-fPIC", "-O2",
               c_out, stub_c, "-o", so_out,
               f"-I{inc}", f"-lpython{ver}", "-lm", "-lpthread"]
        rc, so, se = _run(cmd)
    if rc != 0:
        print(red + "compile failed:\n" + (se or so))
        shutil.rmtree(scratch, ignore_errors=True)
        return
    _stage(f"compiled → {target_so}")

    # sanity — verify the init symbol matches
    if shutil.which("nm"):
        rc2, out2, _ = _run(["nm", "-D", so_out])
        expected = f"PyInit_{mod_name}"
        if rc2 == 0 and expected in out2:
            _stage(f"verified {expected} exported")
        else:
            _stage(f"warning: {expected} not found in exports", ok=False)

    if shutil.which("strip"):
        _run(["strip", "--strip-all", so_out])
    _stage("strip --strip-all")

    if shutil.which("objcopy"):
        for sec in (".comment", ".note.gnu.build-id", ".note.ABI-tag",
                    ".note.gnu.property", ".gnu_debuglink", ".gnu_debugaltlink",
                    ".note.android.ident", ".note.gnu.ident"):
            _run(["objcopy", "--remove-section", sec, so_out])
        _stage("scrub metadata")

    out_dir = _pick_output_dir()
    dest = os.path.join(out_dir, target_so)
    okd, msg = _safe_deploy(so_out, dest)
    if okd: _stage(f"deployed → {dest}")
    else:   _stage(f"deploy failed: {msg}", ok=False)

    shutil.rmtree(scratch, ignore_errors=True)

    _stage_done()
    print(green + f"\n  → {dest}")
    print(yellow + f"\n  import as:  import {mod_name}")
    print(f"  call:       {mod_name}.approval_check_online()")

# ---------------- 3/4: ELF ----------------
def _gen_c(py_file, out_name):
    last = ""
    for pre in _which_cython():
        cmd = pre + ["--embed", "-3", "-X", "language_level=3",
                     "-o", out_name + ".c", py_file]
        rc, so, se = _run(cmd)
        if rc == 0 and os.path.exists(out_name + ".c"):
            return True, ""
        last = se or so
    for pre in _which_cythonize():
        cmd = pre + ["-3", "--embed", "-o", out_name + ".c", py_file]
        rc, so, se = _run(cmd)
        if rc == 0 and os.path.exists(out_name + ".c"):
            return True, ""
        last = se or so
    return False, "no cython produced .c:\n" + last

def _readelf_sections(binary):
    if not shutil.which("readelf"): return []
    rc, so, se = _run(["readelf", "-S", "-W", binary])
    if rc != 0: return []
    out = []
    for line in so.splitlines():
        s = line.strip()
        if s.startswith("[") and "]" in s:
            rest = s.split("]", 1)[1].strip()
            parts = rest.split()
            if len(parts) < 4: continue
            name = parts[0]
            if name.startswith(".") or name.startswith("tx."):
                try:
                    off = int(parts[2], 16); sz = int(parts[3], 16)
                except Exception: continue
                out.append((name, off, sz))
    return out

def _fnv1a_bytes(data):
    h = 1469598103934665603
    for b in data:
        h ^= b; h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h

_AD_MAGIC = 0x414D455441444142

def _patch_admeta(binary):
    with open(binary, "rb") as f:
        blob = f.read()
    magic = struct.pack("<Q", _AD_MAGIC)
    idx = blob.find(magic)
    if idx < 0: return False
    secs = _readelf_sections(binary)
    if not secs: return False
    text = None
    for name, off, sz in secs:
        if name == ".text" or name.startswith("tx."):
            text = (name, off, sz); break
    if not text: return False
    t_off, t_sz = text[1], text[2]
    with open(binary, "rb") as f:
        f.seek(t_off); t_blob = f.read(t_sz)
    h = _fnv1a_bytes(t_blob)
    with open(binary, "r+b") as f:
        f.seek(idx + 8)
        f.write(struct.pack("<QQQ", t_off, t_sz, h))
    return True

def _link(c_file, out_name, hardened):
    inc    = sysconfig.get_path("include")
    libdir = sysconfig.get_config_var("LIBDIR") or ""
    ver    = sysconfig.get_config_var("VERSION")
    cc = shutil.which("cc") or shutil.which("gcc")
    if not cc: return False, "no C compiler"
    base_c = ["-O2", "-fPIC"]
    base_l = [f"-lpython{ver}", "-lm", "-lpthread"]
    if libdir:
        base_l = [f"-L{libdir}", f"-Wl,-rpath,{libdir}"] + base_l
    static_lib = _find_static_libpython() if hardened else None
    if static_lib:
        base_l = [f for f in base_l if not f.startswith("-lpython")]
        base_l = [static_lib] + base_l
        base_c += ["-static-libgcc"]
    if hardened:
        base_c += _cflags()
        base_l = _ldflags() + base_l
        with open("_adstub.h", "w") as f:
            f.write(build_adstub_c()[0])
        base_c = ["-include", "_adstub.h"] + base_c
    cmd = [cc] + base_c + [c_file, "-o", out_name, f"-I{inc}"] + base_l
    rc, so, se = _run(cmd)
    if rc != 0: return False, se or so
    return True, ""

def _post_process_early(binary, hardened):
    if shutil.which("strip"):
        _run(["strip", "--strip-all", binary])
        _stage("strip --strip-all")
    if hardened and shutil.which("objcopy"):
        if T_SECTION_RENAME:
            tname = _rand_section_name("tx")
            dname = _rand_section_name("da")
            rname = _rand_section_name("ro")
            _run(["objcopy", "--rename-section", f".text={tname}",
                  "--rename-section", f".data={dname}",
                  "--rename-section", f".rodata={rname}", binary])
            _stage(f"rename .text→{tname}")
        if T_STRIP_SECTIONS:
            for sec in (".comment", ".note.gnu.build-id", ".note.ABI-tag",
                        ".note.gnu.property", ".gnu_debuglink", ".gnu_debugaltlink",
                        ".note.gnu.gold-version", ".note.go.buildid", ".eh_frame_hdr",
                        ".note.android.ident", ".note.gnu.ident",
                        ".note.android.goldfish"):
                _run(["objcopy", "--remove-section", sec, binary])
            _stage("scrub notes/debug")
        if T_DECOY_SECTIONS:
            try:
                with open(binary, "ab") as f:
                    f.write(os.urandom(512))
                _stage("decoy tail")
            except Exception:
                _stage("decoy failed", ok=False)

def _post_process_late(binary, hardened):
    if hardened and T_SSTRIP:
        if shutil.which("sstrip"):
            _run(["sstrip", binary])
            _stage("sstrip (hdr table gone)")
        else:
            _stage("sstrip not installed — skipped")

def ELF(hardened=False):
    global _STAGE_TOTAL
    _STAGE_TOTAL = 12 if hardened else 5
    _stage_reset()

    print("----------------------------------------------")
    print(reset + "\nFor Example: " + green + "/sdcard/filename.py" + reset)
    src = input("Put File :" + green + " ").strip()
    if not os.path.isfile(src):
        print(red + "File Location Not Found"); return
    _stage("source located")

    base    = os.path.splitext(os.path.basename(src))[0]
    work    = src
    temp_py = None

    try:
        if hardened:
            temp_py = f"_obf_{base}_{os.getpid()}.py"
            inject_anti_debug_py(src, temp_py)
            work = temp_py
            _stage("py anti-debug injected")
        else:
            _stage("source ready")

        ok, err = _gen_c(work, base)
        if not ok: print(red + err); return
        _stage("cython --embed → .c")

        ok, err = _link(base + ".c", base, hardened)
        if not ok and hardened:
            _stage("full link failed, retrying minimal", ok=False)
            rc, so, se = _run([shutil.which("cc") or "cc",
                               "-O2", "-fPIC", "-fno-plt",
                               "-include", "_adstub.h",
                               base + ".c", "-o", base,
                               f"-I{sysconfig.get_path('include')}",
                               f"-lpython{sysconfig.get_config_var('VERSION')}",
                               "-lm", "-lpthread"])
            if rc != 0:
                print(red + "link failed:\n" + (se or so)); return
            ok = True
            _stage("minimal link")
        if not ok:
            print(red + "link failed:\n" + err); return
        if not os.path.exists(base):
            print(red + "binary not produced"); return

        flags_used = []
        if hardened:
            if T_STATIC_LIBPYTHON and _find_static_libpython():
                flags_used.append("static-libpython")
            flags_used += ["LTO", "RELRO", "gc-sections"]
            if _arch() == "x86_64":
                flags_used.append("CET")
            _stage(f"linked ({', '.join(flags_used)})")
        else:
            _stage("linked")

        _post_process_early(base, hardened)

        if hardened and T_SELF_INTEGRITY:
            if _patch_admeta(base):
                _stage(".admeta hash patched")
            else:
                _stage(".admeta patch skipped", ok=False)

        if hardened:
            _stage("watchdogs compiled in")

        _post_process_late(base, hardened)

        out_dir = _pick_output_dir()
        dest = os.path.join(out_dir, os.path.basename(base))
        okd, msg = _safe_deploy(base, dest)
        if okd: _stage(f"deployed → {dest}")
        else:   _stage(f"deploy failed: {msg}", ok=False)

        _stage_done()
        print(green + f"\n  built: {base}" + ("  [MAX v4.8]" if hardened else ""))
        print(green + f"  → {dest}")

    finally:
        for f in (temp_py, "_adstub.h", base + ".c", base + ".o"):
            if f and os.path.exists(f):
                try: os.remove(f)
                except OSError: pass

def main():
    url_wa = "https://api.whatsapp.com/send?phone=+923194999455&text="
    while True:
        print(Banner())
        print("[1] Encrypt Marshal Py3 (lzma + xor + b85)")
        print("[2] Compile Cython " + red + "SO" + reset + " (Anti-Debug + ABI name)")
        print("[3] Compile ELF (Strip)")
        print("[4] Compile ELF " + red + "MAX" + reset + " (Self-Integrity + Watchdogs)")
        print("[0] " + red + "Report Bug" + reset)
        print("----------------------------------------------")
        select = input(" Select : ").strip()
        if select in ("1", "01"):   Marshal(); input("\n[ enter ]")
        elif select in ("2", "02"): Cythonize(); input("\n[ enter ]")
        elif select in ("3", "03"): ELF(False); input("\n[ enter ]")
        elif select in ("4", "04"): ELF(True); input("\n[ enter ]")
        elif select in ("0", "00"):
            if not shutil.which("am"):
                print(red + "no 'am' — Android only"); input("\n[ enter ]"); continue
            p = input(reset + "Problem : " + red)
            _run(["am", "start", url_wa + p])
        else: continue

if __name__ == "__main__":
    main()