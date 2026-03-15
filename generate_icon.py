import zlib
import struct

def generate_png(width, height, color):
    """
    Generates a solid-color PNG file without external libraries.
    color is (R, G, B) tuple.
    """
    def make_chunk(type, data):
        return struct.pack(">I", len(data)) + type + data + struct.pack(">I", zlib.crc32(type + data) & 0xFFFFFFFF)

    # IHDR chunk
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    
    # IDAT chunk (pixel data)
    # Each row starts with a filter byte (0 for none)
    row = b"\x00" + bytes(color) * width
    pixels = row * height
    idat = zlib.compress(pixels)
    
    # PNG signature and chunks
    png_data = b"\x89PNG\r\n\x1a\n"
    png_data += make_chunk(b"IHDR", ihdr)
    png_data += make_chunk(b"IDAT", idat)
    png_data += make_chunk(b"IEND", b"")
    
    return png_data

if __name__ == "__main__":
    # Use the Gordian Key accent color: #7c6af7 (124, 106, 247)
    png_bytes = generate_png(512, 512, (124, 106, 247))
    with open("app_icon.png", "wb") as f:
        f.write(png_bytes)
    print("Generated 512x512 app_icon.png (Solid Gordian Key Accent color).")
