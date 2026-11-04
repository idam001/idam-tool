#!/usr/bin/env python3
"""Robust extraction of Cython LZSS string blobs from .so modules."""
import sys, re
from elftools.elf.elffile import ELFFile
from capstone import *

def sections(f):
    return {s.name: (s['sh_addr'], s['sh_offset'], s['sh_size'], s.data()) for s in f.iter_sections()}

def lzss_decompress(src, dst_len):
    src = bytes(src); dst = bytearray(); pos = 0; out_pos = 0
    try:
        while True:
            if pos >= len(src): return None
            flags = src[pos] | 0xFF00; pos += 1
            while flags & 0x100:
                if flags & 1:
                    if pos >= len(src): return None
                    dst.append(src[pos]); pos += 1; out_pos += 1
                else:
                    if pos + 2 > len(src): return None
                    lo = src[pos]; hi = src[pos+1]; pos += 2
                    if not (lo & 0x80):
                        end_off = lo; ml = hi
                    elif not (hi & 0x80):
                        end_off = 0x80 + (((hi << 2) & 0x180) | (lo & 0x7F)); ml = hi & 0x1F
                    else:
                        if pos >= len(src): return None
                        end_off = 0x80 + ((hi & 0x7F) << 7 | (lo & 0x7F)); ml = src[pos]; pos += 1
                    ml += 3
                    ref = out_pos - end_off - ml
                    if ref < 0: return None
                    dst += dst[ref:ref+ml]; out_pos += ml
                if out_pos >= dst_len:
                    return pos, bytes(dst)
                flags >>= 1
    except Exception:
        return None

def analyze(path):
    raw = open(path, 'rb').read()
    f = open(path, 'rb'); elf = ELFFile(f); secs = sections(elf)
    taddr, toff, tsize, tdata = secs['.text']
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    insns = list(md.disasm(tdata, taddr))

    def v2o(v):
        for name, (addr, soff, size, data) in secs.items():
            if addr and addr <= v < addr + size:
                return soff + (v - addr)
        raise ValueError(hex(v))

    orr_idx = None
    for i, ins in enumerate(insns):
        if ins.mnemonic == 'orr' and '0xff00' in ins.op_str:
            orr_idx = i; break
    assert orr_idx is not None

    # candidate blob: last adr before orr
    blob = None
    for j in range(orr_idx, max(0, orr_idx-80), -1):
        if insns[j].mnemonic == 'adr':
            blob = int(insns[j].op_str.split(', ')[1].strip().replace('#',''), 0); break
    assert blob
    blob_off = v2o(blob)

    # candidate dst_len values from nearby immediates
    cands = set()
    for j in range(max(0, orr_idx-120), min(len(insns), orr_idx+120)):
        ins = insns[j]
        if ins.mnemonic in ('mov', 'cmp'):
            m = re.search(r'#(0x[0-9a-f]+|\d+)$', ins.op_str)
            if m:
                v = int(m.group(1), 0)
                if 100 < v < 200000:
                    cands.add(v)
    results = []
    for d in sorted(cands):
        r = lzss_decompress(raw[blob_off:blob_off+300000], d)
        if r:
            consumed, out = r
            if consumed < 300000:
                results.append((consumed, d, out))
    assert results, 'no successful decompression'
    # prefer result whose consumed length appears as a cmp immediate after the orr
    comp_imms = set()
    for j in range(orr_idx, min(len(insns), orr_idx+300)):
        if insns[j].mnemonic == 'cmp':
            m = re.search(r'#(0x[0-9a-f]+|\d+)$', insns[j].op_str)
            if m: comp_imms.add(int(m.group(1), 0))
    best = None
    for consumed, d, out in results:
        if consumed in comp_imms:
            best = (consumed, d, out); break
    if best is None:
        best = max(results, key=lambda r: r[1])
    comp, dst_len, out = best

    # str index array + count
    idx_addr = None; str_count = None; idx_mask = 0xFFFFFFFF
    for i, ins in enumerate(insns):
        if ins.mnemonic in ('ldrb', 'ldrh', 'ldr') and re.search(r'\], #4$', ins.op_str):
            m = re.search(r'\[(\w+)\]', ins.op_str)
            if not m: continue
            reg = m.group(1)
            for j in range(i, max(0, i-40), -1):
                if insns[j].mnemonic == 'adr' and insns[j].op_str.split(',')[0].strip() == reg:
                    idx_addr = int(insns[j].op_str.split(', ')[1].strip().replace('#',''), 0)
                    break
            if idx_addr:
                # mask from 'and xN, xM, #IMM' shortly after
                for j in range(i, min(len(insns), i+12)):
                    if insns[j].mnemonic == 'and':
                        m3 = re.match(r'x\d+, x\d+, #(0x[0-9a-f]+|\d+)$', insns[j].op_str)
                        if m3: idx_mask = int(m3.group(1), 0)
                last_cmp = None; found = None
                for j in range(i, min(len(insns), i+150)):
                    if insns[j].mnemonic == 'cmp':
                        m2 = re.match(r'x\d+, #(0x[0-9a-f]+|\d+)$', insns[j].op_str)
                        if m2: last_cmp = int(m2.group(1), 0)
                    if insns[j].mnemonic.startswith('b.'):
                        try:
                            t = int(insns[j].op_str.split('#')[-1].strip(), 0)
                        except Exception:
                            continue
                        if t < insns[j].address and last_cmp:
                            found = last_cmp; break
                if found:
                    str_count = found
                    break
    if idx_addr is None:
        # fallback: find index array as adr used with ldrb/ldrh/ldr post-inc anywhere after orr
        for i, ins in enumerate(insns):
            if i > orr_idx and ins.mnemonic in ('ldrb','ldrh','ldr') and re.search(r'\], #4$', ins.op_str):
                m = re.search(r'\[(\w+)\]', ins.op_str)
                if not m: continue
                reg = m.group(1)
                for j in range(i, max(0, i-40), -1):
                    if insns[j].mnemonic == 'adr' and insns[j].op_str.split(',')[0].strip() == reg:
                        idx_addr = int(insns[j].op_str.split(', ')[1].strip().replace('#',''), 0)
                        break
                if idx_addr: break
    assert idx_addr, 'no index array'
    if str_count is None:
        # count = entries until sum of lens would exceed dst_len; scan greedily allowing zeros
        io = v2o(idx_addr)
        lens = []
        pos = 0
        k = 0
        while pos < dst_len:
            l = int.from_bytes(raw[io+4*k:io+4*k+4], 'little') & idx_mask
            lens.append(l); pos += l; k += 1
            if k > 5000: break
        str_count = k
    io = v2o(idx_addr)
    w = 2 if True else 1
    strings = []
    pos = 0
    for k in range(str_count):
        if idx_mask <= 0xFF:
            l = raw[io+4*k] & idx_mask
        elif idx_mask <= 0xFFFF:
            l = int.from_bytes(raw[io+4*k:io+4*k+2], 'little') & idx_mask
        else:
            l = int.from_bytes(raw[io+4*k:io+4*k+4], 'little') & idx_mask
        strings.append(out[pos:pos+l]); pos += l
    return strings, out[pos:], dict(blob=hex(blob), dst_len=dst_len, comp=comp, idx=hex(idx_addr), n=str_count)

if __name__ == '__main__':
    strings, rest, meta = analyze(sys.argv[1])
    print(f'## meta={meta}', file=sys.stderr)
    print(f'## {len(strings)} str constants, trailing bytes region: {len(rest)} bytes', file=sys.stderr)
    for k, s in enumerate(strings):
        print(f'[{k:03d}] {s!r}')
    print('=== TRAILING BYTES REGION ===')
    sys.stdout.buffer.write(rest)
