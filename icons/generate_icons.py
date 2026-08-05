#!/usr/bin/env python3
"""
Generate PWA icons and favicons featuring a camera.

Draws the camera at high resolution with Pillow (no SVG rasterizer needed on
the build machine) and downsamples for crispness. Outputs:
  - icon-192.png, icon-512.png            (PWA, standard)
  - icon-192-maskable.png, icon-512-maskable.png  (PWA, safe-zone padded)
  - apple-touch-icon.png (180)
  - favicon-16.png, favicon-32.png, favicon-48.png
  - favicon.ico (16/32/48 multi-size)

Run:  python3 generate_icons.py
"""
from PIL import Image, ImageDraw
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 4  # supersample factor for anti-aliasing

BG_TOP = (30, 136, 229)     # #1e88e5
BG_BOT = (13, 71, 161)      # #0d47a1
WHITE = (255, 255, 255)
LENS_RING = (13, 71, 161)   # #0d47a1
LENS_MID = (21, 101, 192)   # #1565c0
LENS_LIGHT = (144, 202, 249)  # #90caf9


def vgrad(size, top, bot):
    """Vertical gradient image."""
    img = Image.new("RGB", (1, size), 0)
    for y in range(size):
        t = y / max(1, size - 1)
        img.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img.resize((size, size))


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def draw_camera(size, inset_ratio=0.0):
    """
    Render the camera icon at `size` px. `inset_ratio` shrinks the whole
    artwork toward the center (used for maskable safe-zone padding).
    Returns an RGBA image.
    """
    S = size * SS
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # Background: rounded square with vertical gradient.
    radius = int(S * 0.22)
    grad = vgrad(S, BG_TOP, BG_BOT).convert("RGBA")
    grad.putalpha(rounded_mask(S, radius))
    canvas.alpha_composite(grad)

    d = ImageDraw.Draw(canvas)

    # Coordinate frame for the camera artwork, optionally inset.
    pad = inset_ratio * S
    ox, oy = pad, pad
    W = S - 2 * pad

    def X(fx):  # fractional x within the (inset) art box -> pixel
        return ox + fx * W

    def Y(fy):
        return oy + fy * W

    # --- Camera body (white, rounded) ---
    body = [X(0.17), Y(0.30), X(0.83), Y(0.75)]
    d.rounded_rectangle(body, radius=int(W * 0.08), fill=WHITE)

    # Viewfinder hump on top.
    hump = [X(0.37), Y(0.235), X(0.63), Y(0.315)]
    d.rounded_rectangle(hump, radius=int(W * 0.02), fill=WHITE)

    # --- Lens ---
    cx, cy = X(0.5), Y(0.535)
    r_outer = W * 0.175
    r_mid = W * 0.088
    r_high = W * 0.032

    # Outer ring
    d.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
              fill=LENS_LIGHT, outline=LENS_RING, width=int(W * 0.028))
    # Center glass
    d.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], fill=LENS_MID)
    # Highlight
    hx, hy = cx - r_mid * 0.5, cy - r_mid * 0.5
    d.ellipse([hx - r_high, hy - r_high, hx + r_high, hy + r_high],
              fill=(255, 255, 255, 220))

    # --- Flash indicator ---
    fx, fy = X(0.73), Y(0.375)
    fr = W * 0.030
    d.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=LENS_RING)

    return canvas.resize((size, size), Image.LANCZOS)


def save(img, name):
    path = os.path.join(HERE, name)
    img.save(path)
    print("wrote", name, img.size)


def main():
    # Standard PWA icons
    save(draw_camera(192), "icon-192.png")
    save(draw_camera(512), "icon-512.png")

    # Maskable icons: keep art inside the ~80% safe zone.
    save(draw_camera(192, inset_ratio=0.10), "icon-192-maskable.png")
    save(draw_camera(512, inset_ratio=0.10), "icon-512-maskable.png")

    # Apple touch icon
    save(draw_camera(180), "apple-touch-icon.png")

    # Favicons
    f48 = draw_camera(48)
    f32 = draw_camera(32)
    f16 = draw_camera(16)
    save(f16, "favicon-16.png")
    save(f32, "favicon-32.png")
    save(f48, "favicon-48.png")

    # Multi-size .ico
    ico_path = os.path.join(HERE, "favicon.ico")
    f48.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("wrote favicon.ico")


if __name__ == "__main__":
    main()
