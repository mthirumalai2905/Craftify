"""Paint 16x16 stone-base ore textures and isometric previews."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TEXTURE_DIR = ROOT / "minecraft" / "texture"
SCREEN_DIR = ROOT / "minecraft" / "screenshots"

STONE = [
    (120, 120, 120, 255),
    (110, 110, 110, 255),
    (132, 132, 132, 255),
    (98, 98, 98, 255),
    (142, 142, 142, 255),
    (88, 88, 88, 255),
    (126, 122, 118, 255),
    (104, 108, 104, 255),
]

# Deterministic stone grain so every ore shares the same rock.
STONE_MAP = [
    0, 2, 1, 4, 0, 3, 1, 2, 5, 0, 4, 1, 2, 6, 0, 3,
    1, 5, 0, 2, 6, 1, 4, 0, 2, 3, 1, 7, 0, 2, 5, 1,
    3, 0, 4, 1, 2, 5, 0, 6, 1, 2, 4, 0, 3, 1, 7, 2,
    2, 6, 1, 0, 3, 2, 7, 1, 0, 5, 2, 1, 4, 0, 3, 6,
    0, 1, 5, 2, 0, 4, 1, 3, 2, 0, 6, 1, 2, 5, 0, 4,
    4, 2, 0, 6, 1, 0, 5, 2, 7, 1, 0, 3, 2, 1, 6, 0,
    1, 3, 2, 0, 5, 1, 2, 4, 0, 6, 1, 2, 0, 4, 3, 1,
    5, 0, 7, 1, 2, 3, 0, 1, 4, 2, 0, 5, 1, 2, 0, 6,
    2, 4, 0, 3, 1, 6, 2, 0, 1, 5, 3, 0, 2, 7, 1, 0,
    0, 1, 6, 2, 4, 0, 1, 5, 2, 0, 1, 4, 3, 0, 2, 5,
    3, 2, 1, 0, 5, 2, 7, 0, 1, 3, 2, 6, 0, 1, 4, 2,
    1, 0, 4, 5, 1, 3, 0, 2, 6, 1, 0, 2, 5, 3, 0, 1,
    6, 1, 2, 0, 3, 1, 4, 0, 2, 7, 1, 0, 2, 4, 1, 5,
    0, 5, 1, 2, 0, 6, 1, 3, 0, 2, 4, 1, 0, 2, 6, 0,
    2, 0, 3, 1, 7, 2, 0, 1, 5, 0, 2, 3, 1, 0, 4, 2,
    4, 1, 0, 6, 2, 0, 3, 2, 1, 4, 0, 1, 5, 2, 0, 3,
]

ORES = {
    "coal_ore": {
        "title": "Coal Ore",
        "dark": (12, 12, 14, 255),
        "mid": (28, 28, 30, 255),
        "bright": (52, 52, 56, 255),
        "highlight": (72, 72, 76, 255),
        "blobs": [
            (2, 3, 3, 3),
            (8, 2, 3, 2),
            (4, 8, 4, 3),
            (11, 9, 3, 3),
            (1, 11, 2, 2),
            (12, 4, 2, 2),
        ],
    },
    "iron_ore": {
        "title": "Iron Ore",
        "dark": (122, 78, 48, 255),
        "mid": (184, 124, 78, 255),
        "bright": (216, 168, 118, 255),
        "highlight": (236, 196, 150, 255),
        "blobs": [
            (3, 2, 3, 3),
            (9, 3, 4, 2),
            (2, 8, 3, 3),
            (10, 9, 3, 3),
            (6, 11, 3, 2),
            (12, 6, 2, 2),
        ],
    },
    "diamond_ore": {
        "title": "Diamond Ore",
        "dark": (18, 120, 128, 255),
        "mid": (46, 196, 196, 255),
        "bright": (92, 236, 230, 255),
        "highlight": (186, 255, 252, 255),
        "blobs": [
            (3, 3, 2, 2),
            (9, 2, 3, 3),
            (2, 9, 3, 3),
            (10, 10, 3, 2),
            (6, 6, 3, 3),
            (13, 6, 2, 2),
        ],
    },
    "gold_ore": {
        "title": "Gold Ore",
        "dark": (168, 120, 16, 255),
        "mid": (232, 188, 40, 255),
        "bright": (252, 228, 72, 255),
        "highlight": (255, 246, 164, 255),
        "blobs": [
            (2, 2, 3, 3),
            (8, 4, 3, 2),
            (4, 9, 3, 3),
            (11, 8, 3, 3),
            (7, 12, 3, 2),
            (12, 2, 2, 2),
        ],
    },
    "emerald_ore": {
        "title": "Emerald Ore",
        "dark": (8, 110, 42, 255),
        "mid": (22, 186, 78, 255),
        "bright": (56, 228, 108, 255),
        "highlight": (164, 255, 188, 255),
        "blobs": [
            (4, 2, 2, 3),
            (10, 3, 3, 2),
            (2, 7, 3, 3),
            (9, 9, 3, 3),
            (5, 12, 3, 2),
            (13, 7, 2, 2),
        ],
    },
}


def stone_base(size: int = 16) -> Image.Image:
    img = Image.new("RGBA", (size, size), STONE[0])
    px = img.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = STONE[STONE_MAP[y * size + x] % len(STONE)]
    return img


def paint_blob(px, x0: int, y0: int, w: int, h: int, colors: dict) -> None:
    for y in range(y0, min(16, y0 + h)):
        for x in range(x0, min(16, x0 + w)):
            edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
            if edge:
                px[x, y] = colors["dark"]
            else:
                px[x, y] = colors["mid"]
    cx, cy = x0 + w // 2, y0 + h // 2
    if 0 <= cx < 16 and 0 <= cy < 16:
        px[cx, cy] = colors["bright"]
    hx, hy = min(15, cx + 1), max(0, cy - 1)
    if 0 <= hx < 16 and 0 <= hy < 16 and x0 <= hx < x0 + w and y0 <= hy < y0 + h:
        px[hx, hy] = colors["highlight"]


def ore_texture(name: str) -> Image.Image:
    img = stone_base()
    px = img.load()
    spec = ORES[name]
    for blob in spec["blobs"]:
        paint_blob(px, *blob, spec)
    return img


def isometric_preview(texture: Image.Image) -> Image.Image:
    w, h = 320, 300
    canvas = Image.new("RGBA", (w, h), (246, 246, 248, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((12, 12, w - 13, h - 13), outline=(228, 228, 231, 255), width=1)

    def sample(face: str, u: float, v: float):
        x = min(15, max(0, int(u * 16)))
        y = min(15, max(0, int(v * 16)))
        color = texture.getpixel((x, y))
        if face == "top":
            return tuple(min(255, c + 22) if i < 3 else c for i, c in enumerate(color))
        if face == "left":
            return tuple(max(0, c - 32) if i < 3 else c for i, c in enumerate(color))
        return tuple(max(0, c - 12) if i < 3 else c for i, c in enumerate(color))

    cx, cy = 160, 168
    size = 86

    def project(x: float, y: float, z: float) -> tuple[int, int]:
        sx = cx + (x - z) * size
        sy = cy + (x + z) * size * 0.5 - y * size
        return int(sx), int(sy)

    steps = 16
    for face in ("top", "left", "right"):
        for iy in range(steps):
            for ix in range(steps):
                u0, u1 = ix / steps, (ix + 1) / steps
                v0, v1 = iy / steps, (iy + 1) / steps
                if face == "top":
                    pts = [project(u0, 1, v0), project(u1, 1, v0), project(u1, 1, v1), project(u0, 1, v1)]
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
    return canvas


def lineup(textures: list[tuple[str, Image.Image]]) -> Image.Image:
    cell_w, cell_h = 240, 300
    pad = 24
    cols = len(textures)
    canvas = Image.new("RGBA", (pad + cols * cell_w + pad, cell_h + pad * 2), (246, 246, 248, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((16, 16, canvas.width - 17, canvas.height - 17), outline=(228, 228, 231, 255), width=1)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()

    for index, (title, texture) in enumerate(textures):
        preview = isometric_preview(texture).resize((220, 206), Image.Resampling.LANCZOS)
        x = pad + index * cell_w
        canvas.paste(preview, (x + 10, 28), preview)
        label = title
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + (cell_w - tw) // 2, cell_h + 4), label, fill=(82, 82, 91, 255), font=font)
    return canvas


def cube_model(block_id: str, title: str) -> str:
    return f"""{{
  "credit": "Craftify assessment — {title}",
  "parent": "block/cube_all",
  "texture_size": [16, 16],
  "textures": {{
    "all": "craftify:block/{block_id}",
    "particle": "craftify:block/{block_id}"
  }},
  "elements": [
    {{
      "name": "cube",
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {{
        "north": {{ "uv": [0, 0, 16, 16], "texture": "#all" }},
        "east": {{ "uv": [0, 0, 16, 16], "texture": "#all" }},
        "south": {{ "uv": [0, 0, 16, 16], "texture": "#all" }},
        "west": {{ "uv": [0, 0, 16, 16], "texture": "#all" }},
        "up": {{ "uv": [0, 0, 16, 16], "texture": "#all" }},
        "down": {{ "uv": [0, 0, 16, 16], "texture": "#all" }}
      }}
    }}
  ]
}}
"""


def main() -> None:
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    model_dir = ROOT / "minecraft" / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[tuple[str, Image.Image]] = []
    for name, spec in ORES.items():
        texture = ore_texture(name)
        texture_path = TEXTURE_DIR / f"{name}.png"
        preview_path = SCREEN_DIR / f"{name}_preview.png"
        texture.save(texture_path)
        isometric_preview(texture).save(preview_path)
        (model_dir / f"{name}.json").write_text(cube_model(name, spec["title"]), encoding="utf-8")
        rendered.append((spec["title"], texture))
        print(f"Wrote {texture_path.name}, {name}.json, {preview_path.name}")

    sheet = lineup(rendered)
    sheet_path = SCREEN_DIR / "ore_lineup.png"
    sheet.save(sheet_path)
    print(f"Wrote {sheet_path}")


if __name__ == "__main__":
    main()
