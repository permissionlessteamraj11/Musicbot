import os
import io
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from colorthief import ColorThief
from utils.logger import LOGGER

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
os.makedirs(FONT_DIR, exist_ok=True)
os.makedirs("cache/thumbnails", exist_ok=True)

CARD_W, CARD_H = 800, 280
THUMB_R = 110  # radius for circular thumb


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


async def _download_image(url: str) -> bytes | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    return await r.read()
    except Exception as e:
        LOGGER.warning(f"Thumbnail download failed: {e}")
    return None


def _circle_crop(img: Image.Image, size: int) -> Image.Image:
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    out = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    out.putalpha(mask)
    return out


def _dominant_color(img_bytes: bytes) -> tuple:
    try:
        ct = ColorThief(io.BytesIO(img_bytes))
        return ct.get_color(quality=1)
    except Exception:
        return (30, 30, 50)


def _progress_bar_img(draw: ImageDraw.Draw, x: int, y: int, width: int, pct: float, color: tuple):
    bar_h = 6
    bg_color = (60, 60, 80)
    draw.rounded_rectangle([x, y, x + width, y + bar_h], radius=3, fill=bg_color)
    fill_w = int(width * pct)
    if fill_w > 0:
        draw.rounded_rectangle([x, y, x + fill_w, y + bar_h], radius=3, fill=color)
    # dot
    dot_x = x + fill_w
    draw.ellipse([dot_x - 6, y - 5, dot_x + 6, y + 11], fill=color)


async def make_now_playing_card(
    title: str,
    artist: str,
    duration: int,
    requester: str,
    thumb_url: str = None,
    progress: float = 0.0,
) -> str:
    """Generates a Now Playing card image and returns its file path."""

    thumb_bytes = None
    if thumb_url:
        thumb_bytes = await _download_image(thumb_url)

    def _build() -> str:
        dom_color = _dominant_color(thumb_bytes) if thumb_bytes else (80, 60, 120)
        r, g, b = dom_color

        # ── Background ───────────────────────────────────────────
        bg = Image.new("RGBA", (CARD_W, CARD_H), (15, 15, 25, 255))

        # Blurred album art as full-width background
        if thumb_bytes:
            try:
                art = Image.open(io.BytesIO(thumb_bytes)).convert("RGBA")
                art = art.resize((CARD_W, CARD_H), Image.LANCZOS)
                art = art.filter(ImageFilter.GaussianBlur(radius=22))
                dark_overlay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 160))
                bg = Image.alpha_composite(art, dark_overlay)
            except Exception:
                pass

        draw = ImageDraw.Draw(bg)

        # ── Circular Thumbnail (left) ─────────────────────────────
        thumb_size = THUMB_R * 2
        thumb_x, thumb_y = 30, (CARD_H - thumb_size) // 2

        if thumb_bytes:
            try:
                art_sm = Image.open(io.BytesIO(thumb_bytes)).convert("RGBA")
                circle_img = _circle_crop(art_sm, thumb_size)

                # Glowing ring
                ring = Image.new("RGBA", (thumb_size + 12, thumb_size + 12), (0, 0, 0, 0))
                ring_draw = ImageDraw.Draw(ring)
                ring_draw.ellipse(
                    [0, 0, thumb_size + 12, thumb_size + 12],
                    outline=(r, g, b, 200),
                    width=4,
                )
                bg.paste(ring, (thumb_x - 6, thumb_y - 6), ring)
                bg.paste(circle_img, (thumb_x, thumb_y), circle_img)
            except Exception:
                draw.ellipse(
                    [thumb_x, thumb_y, thumb_x + thumb_size, thumb_y + thumb_size],
                    fill=(r, g, b, 100),
                )
        else:
            draw.ellipse(
                [thumb_x, thumb_y, thumb_x + thumb_size, thumb_y + thumb_size],
                fill=(r, g, b, 100),
            )
            draw.text(
                (thumb_x + thumb_size // 2, thumb_y + thumb_size // 2),
                "♪",
                font=_load_font("Poppins-Bold.ttf", 60),
                fill=(255, 255, 255),
                anchor="mm",
            )

        # ── Text area ─────────────────────────────────────────────
        tx = thumb_x + thumb_size + 30
        text_w = CARD_W - tx - 30

        # NOW PLAYING label
        draw.text(
            (tx, 28),
            "▶  NOW PLAYING",
            font=_load_font("Poppins-Regular.ttf", 13),
            fill=(r, g, b),
        )

        # Title
        title_font = _load_font("Poppins-Bold.ttf", 26)
        title_short = title if len(title) <= 38 else title[:35] + "..."
        draw.text((tx, 55), title_short, font=title_font, fill=(255, 255, 255))

        # Artist
        draw.text(
            (tx, 92),
            f"🎤 {artist}",
            font=_load_font("Poppins-Regular.ttf", 17),
            fill=(200, 200, 220),
        )

        # Requester
        draw.text(
            (tx, 120),
            f"👤 Requested by {requester}",
            font=_load_font("Poppins-Regular.ttf", 14),
            fill=(160, 160, 190),
        )

        # Duration
        from utils.formatters import format_duration
        elapsed = int(progress * duration)
        dur_text = f"⏱ {format_duration(elapsed)}  /  {format_duration(duration)}"
        draw.text(
            (tx, 148),
            dur_text,
            font=_load_font("Poppins-Regular.ttf", 14),
            fill=(180, 180, 210),
        )

        # Progress bar
        _progress_bar_img(draw, tx, 185, text_w, progress, (r, g, b))

        # Waveform decoration (fake bars)
        bar_x = tx
        bar_y_base = CARD_H - 48
        for i in range(35):
            bar_h_val = 4 + (i % 5) * 5 + (i % 3) * 3
            alpha = 80 + (i % 4) * 40
            draw.rectangle(
                [bar_x + i * 7, bar_y_base - bar_h_val, bar_x + i * 7 + 4, bar_y_base],
                fill=(r, g, b, alpha),
            )

        out_path = f"cache/thumbnails/{abs(hash(title + artist))}.png"
        bg.convert("RGB").save(out_path, "PNG", quality=95)
        return out_path

    return await asyncio.get_event_loop().run_in_executor(None, _build)
