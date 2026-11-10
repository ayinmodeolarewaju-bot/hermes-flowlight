"""Build the 1920x1080 hackathon demo from a real hermes CLI transcript and the live page."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/workspace")
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
SANS = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
W, H, FPS = 1920, 1080, 12
BG = (7, 6, 14)
FG = (220, 228, 242)
DIM = (140, 156, 186)
GREEN = (126, 232, 196)
AMBER = (255, 210, 140)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def save_frame(directory: Path, index: int, image: Image.Image) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    image.save(directory / f"{index:05d}.jpg", quality=78, optimize=True)


def terminal_frames(transcript: str, directory: Path, seconds: int = 20) -> None:
    mono = font(FONT, 26)
    small = font(SANS, 18)
    lines = []
    for raw in transcript.splitlines():
        lines.extend(textwrap.wrap(raw, width=92) or [""])
    total = seconds * FPS
    for frame in range(total):
        image = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, W, 56), fill=(16, 16, 28))
        draw.text((36, 16), "hermes  ·  flowlight", font=small, fill=DIM)
        shown = max(0, int((frame - FPS) / 2))
        y = 88
        for line in lines[:shown]:
            color = GREEN if line.startswith("$ ") else FG
            draw.text((48, y), line, font=mono, fill=color)
            y += 36
            if y > H - 80:
                break
        if frame % FPS < FPS // 2:
            draw.rectangle((48, min(y, H - 70), 64, min(y, H - 70) + 26), fill=GREEN)
        save_frame(directory, frame, image)


def title_frames(directory: Path, seconds: int = 8) -> None:
    display = font(BOLD, 86)
    body = font(SANS, 36)
    small = font(SANS, 28)
    total = seconds * FPS
    for frame in range(total):
        image = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(image)
        draw.ellipse((760, 180, 1160, 580), fill=(18, 40, 64))
        draw.ellipse((820, 240, 1100, 520), fill=(90, 190, 255))
        draw.text((760, 640), "Flowlight", font=display, fill=(236, 242, 255))
        draw.text((760, 760), "a Hermes Agent plugin", font=body, fill=(180, 210, 235))
        draw.text((760, 820), "read-only", font=body, fill=AMBER)
        draw.text((760, 900), "github.com/ayinmodeolarewaju-bot/hermes-flowlight", font=small, fill=DIM)
        save_frame(directory, frame, image)


def encode(frames: Path, pattern: str, output: Path, duration: float | None = None) -> None:
    count = len(list(frames.glob("*.jpg")))
    if count == 0:
        raise SystemExit(f"no frames in {frames}")
    rate = FPS if duration is None else count / duration
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", f"{rate:.6f}", "-i", str(frames / pattern),
            "-vf", "fps=12,scale=1920:1080:flags=lanczos,format=yuv420p",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-crf", "26", str(output),
        ],
        check=True,
    )


def main() -> None:
    subprocess.run(
        [
            "bash", "-lc",
            "source ~/.bashrc && export FLOWLIGHT_DATA_DIR=/tmp/flowlight-live2 && "
            "{ echo '$ hermes flowlight watch purefile1686.near and 0xe7030be388b8e247abe0c9fa876673e83fbcbd3c on Base'; "
            "hermes flowlight watch purefile1686.near and 0xe7030be388b8e247abe0c9fa876673e83fbcbd3c on Base; } "
            "> /tmp/flowlight-session.txt",
        ],
        check=True,
    )
    session = Path("/tmp/flowlight-session.txt").read_text(encoding="utf-8").strip()
    (ROOT / "docs" / "demo" / "hermes-session.txt").write_text(session + "\n", encoding="utf-8")
    work = Path("/tmp/flowlight-demo-build")
    if work.exists():
        shutil.rmtree(work)
    terminal = work / "terminal"
    title = work / "title"
    terminal_frames(session, terminal, 20)
    subprocess.run(["node", str(ROOT / "scripts" / "record_browser.mjs")], check=True)
    title_frames(title, 8)
    encode(terminal, "%05d.jpg", work / "terminal.mp4")
    encode(Path("/tmp/flowlight-browser"), "%05d.jpg", work / "browser.mp4", duration=46)
    encode(title, "%05d.jpg", work / "title.mp4")
    listing = work / "list.txt"
    listing.write_text(
        "file 'terminal.mp4'\nfile 'browser.mp4'\nfile 'title.mp4'\n",
        encoding="utf-8",
    )
    raw = ROOT / "docs" / "demo" / "flowlight-demo-raw.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-crf", "26", str(raw),
        ],
        check=True,
        cwd=work,
    )
    captions = ROOT / "docs" / "demo" / "flowlight-demo.srt"
    captions.write_text(
        "\n".join([
            "1", "00:00:00,000 --> 00:00:08,000",
            "ask hermes to watch purefile1686.near and a busy base wallet",
            "",
            "2", "00:00:08,000 --> 00:00:20,000",
            "the summary names the largest inflow, with thousands separators",
            "",
            "3", "00:00:20,000 --> 00:00:36,000",
            "live arcs. cyan is usdc. the green node is the quiet near account",
            "",
            "4", "00:00:36,000 --> 00:00:50,000",
            "scrub back, then play the window again",
            "",
            "5", "00:00:50,000 --> 00:00:66,000",
            "click the largest inflow. the panel matches, with an explorer link",
            "",
            "6", "00:00:66,000 --> 00:01:16,000",
            "flowlight. a hermes agent plugin. read-only.",
            "",
        ]),
        encoding="utf-8",
    )
    styled = ROOT / "docs" / "demo" / "flowlight-demo.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw),
            "-vf",
            "subtitles=" + str(captions) + ":force_style='FontName=DejaVu Sans,FontSize=22,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101018,BorderStyle=1,Outline=2,"
            "Alignment=2,MarginV=56'",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-crf", "26", str(styled),
        ],
        check=True,
    )
    for jpg, png in (
        ("/tmp/flowlight-wide.jpg", ROOT / "docs" / "screenshots" / "live-flows.png"),
        ("/tmp/flowlight-detail.jpg", ROOT / "docs" / "screenshots" / "arc-detail.png"),
    ):
        if Path(jpg).exists():
            subprocess.run(
                ["ffmpeg", "-y", "-i", jpg, str(png)],
                check=True,
            )
    banner = ROOT / "docs" / "screenshots" / "banner.png"
    if (ROOT / "docs" / "screenshots" / "live-flows.png").exists():
        shutil.copy(ROOT / "docs" / "screenshots" / "live-flows.png", banner)


if __name__ == "__main__":
    main()
