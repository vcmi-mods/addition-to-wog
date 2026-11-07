import struct, zlib, os, sys

LOD = '/home/igor/.local/share/vcmi/Data/H3sprite.lod'

def lod_get(path, name):
    data = open(path, 'rb').read()
    pos, ents = 92, {}
    while pos + 32 <= len(data):
        raw = data[pos:pos+16].split(b'\x00')[0]
        if not raw or not all(32 <= c < 127 for c in raw):
            break
        off, size, typ, comp = struct.unpack_from('<4i', data, pos+16)
        ents[raw.decode().lower()] = (off, size, typ, comp)
        pos += 32
    off, size, typ, comp = ents[name.lower()]
    raw = data[off:off+size]
    if comp and comp < size:
        raw = zlib.decompress(raw)
    return raw

def parse_def(raw):
    """Возвращает (palette, {blockID: [frame_offsets]})"""
    it = 0
    typ = struct.unpack_from('<i', raw, it)[0]; it += 4
    _w, _h = struct.unpack_from('<2i', raw, it); it += 8
    totalBlocks = struct.unpack_from('<i', raw, it)[0]; it += 4
    palette = []
    for i in range(256):
        palette.append((raw[it], raw[it+1], raw[it+2])); it += 3

    blocks = {}
    for _ in range(totalBlocks):
        blockID = struct.unpack_from('<i', raw, it)[0]; it += 4
        totalEntries = struct.unpack_from('<i', raw, it)[0]; it += 4
        it += 8  # 8 неизвестных байт
        names = []
        for j in range(totalEntries):
            n = raw[it:it+13].split(b'\x00')[0].decode('latin1')
            names.append(n); it += 13
        offsets = []
        for j in range(totalEntries):
            offsets.append(struct.unpack_from('<i', raw, it)[0]); it += 4
        blocks[blockID] = (names, offsets)
    return palette, blocks

def decode_frame(raw, frame_off, palette):
    """Декодирует один кадр. Возвращает (w, h, rgba) или None."""
    size, fmt, fullW, fullH, w, h, left, top = struct.unpack_from('<4I4i', raw, frame_off)
    base = frame_off + 32
    if fmt == 1 and w > fullW and h > fullH:
        left = top = 0
        w, h = fullW, fullH
        base = frame_off + 16

    px = bytearray(w * h * 4)
    cur = base

    def put_pixel(idx, ci):
        if ci == 0:
            return  # прозрачный
        r, g, b = palette[ci]
        o = idx * 4
        px[o] = r; px[o+1] = g; px[o+2] = b; px[o+3] = 255

    for y in range(h):
        row = []
        if fmt == 0:
            for x in range(w):
                row.append(raw[cur]); cur += 1
        elif fmt == 1:
            rowstart = base + struct.unpack_from('<I', raw, base + 4*y)[0]
            cur = rowstart
            while len(row) < w:
                seg = raw[cur]; ln = raw[cur+1] + 1; cur += 2
                if seg == 0xFF:
                    row.extend(raw[cur:cur+ln]); cur += ln
                else:
                    row.extend([seg]*ln)
        elif fmt == 2:
            if y == 0:
                cur = base + struct.unpack_from('<H', raw, base)[0]
            while len(row) < w:
                s = raw[cur]; cur += 1
                code = s // 32; ln = (s & 31) + 1
                if code == 7:
                    row.extend(raw[cur:cur+ln]); cur += ln
                else:
                    row.extend([code]*ln)
        elif fmt == 3:
            rowoff = base + struct.unpack_from('<H', raw, base + y*2*(w//32))[0]
            cur = rowoff
            while len(row) < w:
                s = raw[cur]; cur += 1
                code = s // 32; ln = (s & 31) + 1
                if code == 7:
                    row.extend(raw[cur:cur+ln]); cur += ln
                else:
                    row.extend([code]*ln)
        else:
            return None
        for x in range(min(w, len(row))):
            put_pixel(y * w + x, row[x])
    return w, h, bytes(px)

def write_png(path, w, h, rgba):
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    raw = b''.join(b'\x00' + rgba[y*w*4:(y+1)*w*4] for y in range(h))
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(raw, 9))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)

if __name__ == '__main__':
    raw = lod_get(LOD, 'Artifact.def')
    palette, blocks = parse_def(raw)
    print('блоки:', sorted(blocks.keys()))
    for bid, (names, offsets) in blocks.items():
        print('блок %d: кадров %d, первые имена: %s' % (bid, len(names), names[:3]))
