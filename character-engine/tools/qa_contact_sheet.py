#!/usr/bin/env python3
"""Build contact sheets from rendered episode frames for quick visual QA."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FONT_DIR = "/System/Library/Fonts/Supplemental/"


def font(size=26):
    try:
        return ImageFont.truetype(FONT_DIR + "Arial Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def sample_frames(line_dir):
    frames = sorted(line_dir.glob("f*.png"))
    if not frames:
        return []
    picks = [0, len(frames) // 2, len(frames) - 1]
    return [frames[i] for i in sorted(set(picks))]


def build_sheet(episode_dir, out_path, thumb_w=360):
    line_dirs = sorted((episode_dir / "frames").glob("line*"))
    samples = []
    for line_dir in line_dirs:
        for frame in sample_frames(line_dir):
            samples.append((line_dir.name, frame))
    if not samples:
        raise SystemExit(f"no rendered frames found under {episode_dir / 'frames'}")

    first = Image.open(samples[0][1]).convert("RGB")
    thumb_h = round(first.height * (thumb_w / first.width))
    label_h = 36
    cols = 3
    rows = (len(samples) + cols - 1) // cols
    pad = 18
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad), (12, 14, 22))
    draw = ImageDraw.Draw(sheet)
    fnt = font(22)

    for idx, (line_name, frame_path) in enumerate(samples):
        row, col = divmod(idx, cols)
        x = pad + col * (thumb_w + pad)
        y = pad + row * (thumb_h + label_h + pad)
        img = Image.open(frame_path).convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.paste(img, (x, y))
        draw.text((x + 6, y + thumb_h + 7), f"{line_name} / {frame_path.name}", font=fnt, fill=(225, 235, 245))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    print(f"wrote {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_dir")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    episode_dir = Path(args.episode_dir).resolve()
    out_path = Path(args.out).resolve() if args.out else episode_dir / "qa_contact_sheet.jpg"
    build_sheet(episode_dir, out_path)


if __name__ == "__main__":
    main()
