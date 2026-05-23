import struct
import zlib
import os

def create_png(width, height, color=(10, 14, 23)):
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    r, g, b = color
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            raw += struct.pack('BBB', r, g, b)

    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')

    return b'\x89PNG\r\n\x1a\n' + ihdr + idat + iend

def create_icon(width, output_path):
    bg = (10, 14, 23)
    accent = (66, 133, 244)
    r, g, b = bg
    a_r, a_g, a_b = accent

    raw = b''
    for y in range(width):
        raw += b'\x00'
        for x in range(width):
            cx, cy = width / 2, width / 2
            r_inner = width * 0.2
            r_outer = width * 0.42
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d < r_inner:
                raw += struct.pack('BBB', a_r, a_g, a_b)
            elif d < r_outer:
                t = (d - r_inner) / (r_outer - r_inner)
                cr = int(r + (a_r - r) * (1 - t))
                cg = int(g + (a_g - g) * (1 - t))
                cb = int(b + (a_b - b) * (1 - t))
                raw += struct.pack('BBB', cr, cg, cb)
            else:
                raw += struct.pack('BBB', r, g, b)

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, width, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')

    png_data = b'\x89PNG\r\n\x1a\n' + ihdr + idat + iend
    with open(output_path, 'wb') as f:
        f.write(png_data)
    print(f'  Created: {output_path} ({len(png_data)} bytes)')

if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    create_icon(192, os.path.join(base, 'icon-192.png'))
    create_icon(512, os.path.join(base, 'icon-512.png'))
    print('Icons generated.')