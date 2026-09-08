"""Generate the Magic Crystal Block texture and a simple isometric preview."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
TEXTURE = ROOT / "minecraft" / "texture" / "magic_crystal.png"
PREVIEW = ROOT / "minecraft" / "screenshots" / "magic_crystal_preview.png"


def crystal_texture(size: int = 16) -> Image.Image:
    img = Image.new("RGBA", (size, size), (8, 18, 28, 255))
    px = img.load()
    palette = {
        "edge": (18, 42, 58, 255),
        "dark": (12, 64, 78, 255),
        "mid": (24, 140, 156, 255),
        "bright": (86, 224, 214, 255),
        "core": (210, 255, 248, 255),
        "facet": (40, 176, 188, 255),
    }
    for y in range(size):
        for x in range(size):
            if x in (0, size - 1) or y in (0, size - 1):
                px[x, y] = palette["edge"]
            elif x in (1, size - 2) or y in (1, size - 2):
                px[x, y] = palette["dark"]
            else:
                px[x, y] = palette["mid"]

    for x, y in ((4, 4), (5, 4), (4, 5), (11, 4), (10, 5), (5, 11), (11, 11)):
        px[x, y] = palette["facet"]
    for x, y in ((7, 6), (8, 6), (6, 7), (7, 7), (8, 7), (9, 7), (7, 8), (8, 8)):
        px[x, y] = palette["bright"]
    px[7, 7] = palette["core"]
    px[8, 7] = palette["core"]
    return img


def isometric_preview(texture: Image.Image) -> Image.Image:
    scale = 18
    tex = texture.resize((16 * scale, 16 * scale), Image.NEAREST)
    w, h = 520, 360
    canvas = Image.new("RGBA", (w, h), (246, 246, 248, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((24, 24, w - 25, h - 25), outline=(228, 228, 231, 255), width=1)

    def sample(face: str, u: float, v: float) -> tuple[int, int, int, int]:
        x = min(15, max(0, int(u * 16)))
        y = min(15, max(0, int(v * 16)))
        color = texture.getpixel((x, y))
        if face == "top":
            return tuple(min(255, c + 28) if i < 3 else c for i, c in enumerate(color))  # type: ignore
        if face == "left":
            return tuple(max(0, c - 36) if i < 3 else c for i, c in enumerate(color))  # type: ignore
        return tuple(max(0, c - 14) if i < 3 else c for i, c in enumerate(color))  # type: ignore

    cx, cy = 260, 188
    size = 92

    def project(x: float, y: float, z: float) -> tuple[int, int]:
        sx = cx + (x - z) * size
        sy = cy + (x + z) * size * 0.5 - y * size
        return int(sx), int(sy)

    steps = 16
    for face, corners in (
        ("top", ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1))),
        ("left", ((0, 1, 1), (0, 1, 0), (0, 0, 0), (0, 0, 1))),
        ("right", ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0))),
    ):
        for iy in range(steps):
            for ix in range(steps):
                u0, u1 = ix / steps, (ix + 1) / steps
                v0, v1 = iy / steps, (iy + 1) / steps
                if face == "top":
                    pts = [
                        project(u0, 1, v0),
                        project(u1, 1, v0),
                        project(u1, 1, v1),
                        project(u0, 1, v1),
                    ]
                elif face == "left":
                    pts = [
                        project(0, 1 - v0, 1 - u0),
                        project(0, 1 - v0, 1 - u1),
                        project(0, 1 - v1, 1 - u1),
                        project(0, 1 - v1, 1 - u0),
                    ]
                else:
                    pts = [
                        project(u0, 1 - v0, 0),
                        project(u1, 1 - v0, 0),
                        project(u1, 1 - v1, 0),
                        project(u0, 1 - v1, 0),
                    ]
                draw.polygon(pts, fill=sample(face, (u0 + u1) / 2, (v0 + v1) / 2))

    _ = tex
    return canvas


def main() -> None:
    TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    texture = crystal_texture(16)
    texture.save(TEXTURE)
    isometric_preview(texture).save(PREVIEW)
    print(f"Wrote {TEXTURE}")
    print(f"Wrote {PREVIEW}")


if __name__ == "__main__":
    main()
