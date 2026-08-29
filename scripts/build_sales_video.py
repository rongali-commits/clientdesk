from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

SHARED_PYDEPS = Path(__file__).resolve().parents[3] / "tmp" / "upwork-video" / "pydeps"
sys.path.insert(0, str(SHARED_PYDEPS))

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
WORK = WORKSPACE / "tmp" / "clientdesk-video"
FRAMES = WORK / "frames"
ASSETS = ROOT / "sales-assets"
OUTPUT = ASSETS / "ClientDesk-Marketplace-Demo.mp4"
NARRATION = ASSETS / "ClientDesk-Marketplace-Narration.mp3"
SUBTITLES = ASSETS / "ClientDesk-Marketplace-Narration.srt"
FRAMES.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1280, 720
BG = "#09110D"
PANEL = "#15241B"
CREAM = "#F5F2E9"
MUTED = "#ABB5AE"
LIME = "#C9FF55"
FOREST = "#10291D"
FONT_REGULAR = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_SEMIBOLD = Path(r"C:\Windows\Fonts\seguisb.ttf")
VOICE = "en-US-EmmaMultilingualNeural"
NARRATION_TEXT = """Give every client one clear place to move work forward with ClientDesk.

ClientDesk replaces scattered emails, file links, approval threads, and invoice reminders with one branded workspace.

Every customer receives a private portal showing progress, milestones, updates, deliverables, approvals, and invoice status.

Your team manages every active workspace from a focused studio dashboard.

Apply your business name, colors, welcome copy, and support details without rebuilding the product.

Choose your package and launch ClientDesk for your agency, consultancy, or service business with Noerong."""


def font(size: int, semibold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_SEMIBOLD if semibold else FONT_REGULAR), size)


def rounded_panel(canvas: Image.Image, box: tuple[int, int, int, int], radius: int = 26) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    x1, y1, x2, y2 = box
    shadow_draw.rounded_rectangle(
        (x1 + 8, y1 + 12, x2 + 8, y2 + 12), radius, fill=(0, 0, 0, 115)
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(canvas).rounded_rectangle(
        box, radius, fill=PANEL, outline="#314039", width=2
    )


def brand_header(canvas: Image.Image, label: str) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((48, 28, 88, 68), 12, fill=LIME)
    draw.text((61, 33), "C", font=font(24, True), fill=FOREST)
    draw.text((102, 31), "ClientDesk", font=font(25, True), fill=CREAM)
    pill_width = draw.textbbox((0, 0), label.upper(), font=font(15, True))[2] + 34
    draw.rounded_rectangle(
        (WIDTH - 48 - pill_width, 32, WIDTH - 48, 64),
        16,
        fill="#1A2A21",
        outline="#385043",
    )
    draw.text(
        (WIDTH - 48 - pill_width + 17, 38),
        label.upper(),
        font=font(15, True),
        fill=LIME,
    )


def fit_scene(source: Path, target: Path, label: str, centering: tuple[float, float] = (0.5, 0.46)) -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    brand_header(canvas, label)
    box = (38, 84, WIDTH - 38, HEIGHT - 34)
    rounded_panel(canvas, box)

    shot = Image.open(source).convert("RGB")
    fitted = ImageOps.fit(
        shot,
        (1168, 574),
        method=Image.Resampling.LANCZOS,
        centering=centering,
    )
    x = (WIDTH - fitted.width) // 2
    y = 100
    mask = Image.new("L", fitted.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, fitted.width, fitted.height), 18, fill=255
    )
    canvas.paste(fitted, (x, y), mask)
    canvas.convert("RGB").save(target, quality=95)


def make_title(target: Path) -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)
    for x in range(0, WIDTH, 80):
        draw.line((x, 0, x, HEIGHT), fill="#121B16", width=1)
    for y in range(0, HEIGHT, 80):
        draw.line((0, y, WIDTH, y), fill="#121B16", width=1)

    draw.rounded_rectangle((70, 72, 116, 118), 14, fill=LIME)
    draw.text((84, 78), "C", font=font(26, True), fill=FOREST)
    draw.text((132, 76), "CLIENTDESK", font=font(23, True), fill=CREAM)
    draw.rounded_rectangle((70, 175, 250, 215), 20, fill="#18291F", outline="#385043")
    draw.ellipse((89, 189, 101, 201), fill=LIME)
    draw.text((113, 183), "LIVE PRODUCT", font=font(16, True), fill=LIME)

    draw.text((70, 255), "Give every client", font=font(58, True), fill=CREAM)
    draw.text((70, 323), "one clear place to move.", font=font(58, True), fill=LIME)
    draw.text(
        (72, 421),
        "White-label project delivery, approvals, files, and invoices",
        font=font(27),
        fill=MUTED,
    )

    pills = ["CLIENT PORTAL", "APPROVALS", "INVOICE VISIBILITY"]
    x = 70
    for pill in pills:
        width = draw.textbbox((0, 0), pill, font=font(15, True))[2] + 38
        draw.rounded_rectangle(
            (x, 512, x + width, 552), 20, fill=PANEL, outline="#385043"
        )
        draw.text((x + 19, 520), pill, font=font(15, True), fill="#D7DED9")
        x += width + 14

    canvas.convert("RGB").save(target, quality=95)


def make_outro(target: Path) -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((920, -140, 1320, 260), fill="#193222")
    draw.ellipse((-160, 520, 240, 920), fill="#273118")

    draw.rounded_rectangle((70, 70, 116, 116), 14, fill=LIME)
    draw.text((84, 76), "C", font=font(26, True), fill=FOREST)
    draw.text((132, 74), "CLIENTDESK", font=font(23, True), fill=CREAM)

    draw.text((70, 213), "Deliver a calmer", font=font(58, True), fill=CREAM)
    draw.text((70, 281), "client experience.", font=font(58, True), fill=LIME)
    draw.text(
        (72, 388),
        "Progress  •  Files  •  Approvals  •  Invoices  •  One workspace",
        font=font(27),
        fill=MUTED,
    )

    draw.rounded_rectangle((70, 490, 470, 558), 34, fill=LIME)
    draw.text(
        (108, 507),
        "CHOOSE A PACKAGE TO START",
        font=font(20, True),
        fill=FOREST,
    )
    canvas.convert("RGB").save(target, quality=95)


async def create_narration() -> None:
    communicator = edge_tts.Communicate(
        NARRATION_TEXT,
        voice=VOICE,
        rate="-10%",
        volume="+0%",
        boundary="SentenceBoundary",
    )
    subtitle_maker = edge_tts.SubMaker()
    with NARRATION.open("wb") as audio_file:
        async for message in communicator.stream():
            if message["type"] == "audio":
                audio_file.write(message["data"])
            elif message["type"] == "SentenceBoundary":
                subtitle_maker.feed(message)
    SUBTITLES.write_text(subtitle_maker.get_srt(), encoding="utf-8")


def render_video() -> Path:
    asyncio.run(create_narration())

    title = FRAMES / "00-title.png"
    landing = FRAMES / "01-landing.png"
    portal = FRAMES / "02-portal.png"
    dashboard = FRAMES / "03-dashboard.png"
    brand = FRAMES / "04-brand.png"
    outro = FRAMES / "05-outro.png"

    make_title(title)
    fit_scene(ASSETS / "01-product-landing.png", landing, "PRODUCT OVERVIEW", (0.5, 0.42))
    fit_scene(ASSETS / "02-client-portal.png", portal, "PRIVATE CLIENT PORTAL", (0.5, 0.45))
    fit_scene(ASSETS / "03-studio-dashboard.png", dashboard, "STUDIO DASHBOARD", (0.5, 0.43))
    fit_scene(ASSETS / "04-brand-settings.png", brand, "WHITE-LABEL SETTINGS", (0.5, 0.5))
    make_outro(outro)

    scenes = [
        (title, 3.2),
        (landing, 7.4),
        (portal, 9.0),
        (dashboard, 7.4),
        (brand, 6.0),
        (outro, 8.0),
    ]

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg, "-y"]
    for path, duration in scenes:
        command.extend(["-loop", "1", "-t", f"{duration:.1f}", "-i", str(path)])
    command.extend(["-i", str(NARRATION)])

    filters: list[str] = []
    for index, (_, duration) in enumerate(scenes):
        fade_out = max(duration - 0.25, 0)
        filters.append(
            f"[{index}:v]fps=30,format=yuv420p,"
            f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out:.2f}:d=0.25,"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
    joined = "".join(f"[v{i}]" for i in range(len(scenes)))
    filters.append(f"{joined}concat=n={len(scenes)}:v=1:a=0[base]")
    subtitle_path = SUBTITLES.relative_to(WORKSPACE).as_posix()
    filters.append(
        "[base]subtitles=filename='"
        + subtitle_path
        + "':force_style='FontName=Segoe UI,FontSize=16,PrimaryColour=&H00FFFFFF,"
        "BackColour=&H78000000,OutlineColour=&H78000000,BorderStyle=3,Outline=1,"
        "Shadow=0,MarginL=90,MarginR=90,MarginV=18,Alignment=2'[vout]"
    )
    audio_index = len(scenes)
    filters.append(f"[{audio_index}:a]apad=pad_dur=3[aout]")

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            "41.0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-r",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ]
    )
    subprocess.run(command, cwd=WORKSPACE, check=True)
    return OUTPUT


if __name__ == "__main__":
    print(render_video())
