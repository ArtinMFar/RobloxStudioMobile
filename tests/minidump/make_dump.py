# Synthetic x64 minidump: Roblox-like modules + an access violation inside RobloxStudioBeta.exe.
import struct, sys
def mdstring(s):
    b = s.encode("utf-16-le")
    return struct.pack("<I", len(b)) + b + b"\0\0"
modules = [(0x140000000, 0x9000000, r"C:\Program Files\Roblox Studio\RobloxStudioBeta.exe"),
           (0x6FFFFFC00000, 0x200000, r"C:\windows\system32\ntdll.dll")]
out = bytearray(32)                       # header, filled in later
dir_rva = len(out); out += bytes(12 * 3)  # 3 directory entries
names = []
for _, _, n in modules:
    names.append(len(out)); out += mdstring(n)
while len(out) % 8: out += b"\0"
ml_rva = len(out)
out += struct.pack("<I", len(modules))
for (base, size, _), name_rva in zip(modules, names):
    m = struct.pack("<QIIII", base, size, 0, 0, name_rva) + bytes(52 + 8 * 4)
    assert len(m) == 108
    out += m
ml_size = len(out) - ml_rva
ex_rva = len(out)
params = [1, 0x10] + [0] * 13
out += struct.pack("<II", 0x24c, 0)                                    # ThreadId, alignment
out += struct.pack("<IIQQII", 0xC0000005, 0, 0, 0x140123456, 2, 0)    # code, flags, record, address, nparams, align
out += struct.pack("<15Q", *params)
out += struct.pack("<II", 0, 0)                                        # thread context location
ex_size = len(out) - ex_rva
struct.pack_into("<IIII", out, 0, 0x504d444d, 0xa793, 3, dir_rva)
struct.pack_into("<III", out, dir_rva, 3, 0, 0)                        # ThreadListStream, empty
struct.pack_into("<III", out, dir_rva + 12, 4, ml_size, ml_rva)
struct.pack_into("<III", out, dir_rva + 24, 6, ex_size, ex_rva)
open(sys.argv[1], "wb").write(out)
