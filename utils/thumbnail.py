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

CARD_W, CARD_H = 900, 350
THUMB_R = 140


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
        return (100, 100, 255)


def _progress_bar_img(draw: ImageDraw.Draw, x: int, y: int, width: int, pct: float, color: tuple):
    bar_h = 4
    bg_color = (40, 40, 60)
    draw.rounded_rectangle([x, y, x + width, y + bar_h], radius=2, fill=bg_color)
    fill_w = int(width * pct)
    if fill_w > 0:
        draw.rounded_rectangle([x, y, x + fill_w, y + bar_h], radius=2, fill=color)
    # small glow dot
    dot_x = x + fill_w
    draw.ellipse([dot_x - 4, y - 3, dot_x + 4, y + 7], fill=color)


async def make_now_playing_card(
    title: str,
    artist: str,
    duration: int,
    requester: str,
    thumb_url: str = None,
    progress: float = 0.0,
) -> str:
    """Generates a professional Now Playing card image."""

    thumb_bytes = None
    if thumb_url:
        thumb_bytes = await _download_image(thumb_url)

    def _build() -> str:
        dom_color = _dominant_color(thumb_bytes) if thumb_bytes else (100, 120, 255)
        r, g, b = dom_color

        # Background - Deep dark elegant blue/black
        bg = Image.new("RGBA", (CARD_W, CARD_H), (10, 10, 15, 255))

        if thumb_bytes:
            try:
                art = Image.open(io.BytesIO(thumb_bytes)).convert("RGBA")
                art = art.resize((CARD_W, CARD_H), Image.LANCZOS)
                art = art.filter(ImageFilter.GaussianBlur(radius=40))
                dark_overlay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 180))
                bg = Image.alpha_composite(art, dark_overlay)
            except Exception:
                pass

        draw = ImageDraw.Draw(bg)

        # Large Circular Thumbnail
        thumb_size = THUMB_R * 2
        thumb_x, thumb_y = 40, (CARD_H - thumb_size) // 2

        if thumb_bytes:
            try:
                art_sm = Image.open(io.BytesIO(thumb_bytes)).convert("RGBA")
                circle_img = _circle_crop(art_sm, thumb_size)

                # Outer glow ring
                for i in range(1, 10):
                    alpha = int(100 / i)
                    draw.ellipse(
                        [thumb_x - i, thumb_y - i, thumb_x + thumb_size + i, thumb_y + thumb_size + i],
                        outline=(r, g, b, alpha),
                        width=1
                    )

                bg.paste(circle_img, (thumb_x, thumb_y), circle_img)
            except Exception:
                draw.ellipse([thumb_x, thumb_y, thumb_x+thumb_size, thumb_y+thumb_size], fill=(r,g,b, 100))
        else:
             draw.ellipse([thumb_x, thumb_y, thumb_x+thumb_size, thumb_y+thumb_size], fill=(40,40,60))

        # Text Area
        tx = thumb_x + thumb_size + 50
        text_w = CARD_W - tx - 50

        # Subtitle
        draw.text(
            (tx, 60),
            "SYSTEM ACTIVE STREAM",
            font=_load_font("Montserrat-Regular.ttf", 14),
            fill=(r, g, b),
        )

        # Title
        title_font = _load_font("Montserrat-Bold.ttf", 36)
        title_short = title if len(title) <= 30 else title[:27] + "..."
        draw.text((tx, 90), title_short, font=title_font, fill=(255, 255, 255))

        # Artist
        draw.text(
            (tx, 145),
            f"PERFORMER: {artist.upper()}",
            font=_load_font("Montserrat-Regular.ttf", 18),
            fill=(180, 180, 200),
        )

        # Requester & Specs
        draw.text(
            (tx, 180),
            f"AUTHORIZED BY: {requester.upper()}",
            font=_load_font("Montserrat-Regular.ttf", 14),
            fill=(140, 140, 160),
        )

        draw.text(
            (tx, 205),
            "QUALITY: 320KBPS | SAMPLE RATE: 48KHZ",
            font=_load_font("Montserrat-Bold.ttf", 12),
            fill=(r, g, b, 180),
        )

        # Progress bar
        bar_y = 250
        _progress_bar_img(draw, tx, bar_y, text_w, progress, (r, g, b))

        # Time labels
        from utils.formatters import format_duration
        elapsed = int(progress * duration)
        draw.text((tx, bar_y + 15), format_duration(elapsed), font=_load_font("Montserrat-Regular.ttf", 12), fill=(160, 160, 180))
        draw.text((tx + text_w, bar_y + 15), format_duration(duration), font=_load_font("Montserrat-Regular.ttf", 12), fill=(160, 160, 180), anchor="ra")

        out_path = f"cache/thumbnails/{abs(hash(title + artist))}.png"
        bg.convert("RGB").save(out_path, "PNG", quality=95)
        return out_path

    return await asyncio.get_event_loop().run_in_executor(None, _build)
