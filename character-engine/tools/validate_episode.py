#!/usr/bin/env python3
"""Validate a Bot That Lyfe Nate & Kai episode manifest before rendering."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import rig_pose  # noqa: E402

SPEAKERS = {"nate", "kai"}
MOODS = {"neutral", "smile", "halflid", "brows_up"}
MOVES = {"pace_out", "pace_back"}
SCREEN_TYPES = {"text", "stat", "timeline", "table", "quote", "image", "meme"}


def err(errors, path, msg):
    errors.append(f"{path}: {msg}")


def require(obj, key, path, errors):
    if key not in obj:
        err(errors, path, f"missing required field {key!r}")
        return None
    return obj[key]


def valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_screen(spec, path, errors, base_dir):
    if not isinstance(spec, dict):
        err(errors, path, "screen must be an object")
        return
    stype = spec.get("type", "text")
    if stype not in SCREEN_TYPES:
        err(errors, path + ".type", f"unknown screen type {stype!r}")
        return
    required = {
        "stat": ["value", "label"],
        "timeline": ["events"],
        "table": ["rows"],
        "quote": ["quote", "attribution"],
        "image": ["path"],
        "meme": ["path"],
    }.get(stype, [])
    for key in required:
        require(spec, key, path, errors)
    if stype in ("image", "meme") and "path" in spec:
        image_path = Path(spec["path"]).expanduser()
        if not image_path.is_absolute():
            image_path = base_dir / image_path
        if not image_path.exists():
            err(errors, path + ".path", f"image does not exist: {image_path}")
    if stype == "table":
        for i, row in enumerate(spec.get("rows", [])):
            if not isinstance(row, list) or len(row) != 2:
                err(errors, f"{path}.rows[{i}]", "table rows must be 2-item arrays")


def validate_episode(ep, base_dir):
    errors = []
    for key in ("episode", "title", "lines"):
        require(ep, key, "$", errors)
    # sources is optional — BTL episodes are standalone scripts, not derived
    # from a published article, so a line often has nothing to cite.
    sources = ep.get("sources", [])
    if not isinstance(sources, list):
        err(errors, "$.sources", "must be an array")
        sources = []
    source_ids = set()
    for i, src in enumerate(sources):
        path = f"$.sources[{i}]"
        if not isinstance(src, dict):
            err(errors, path, "source must be an object")
            continue
        sid = require(src, "id", path, errors)
        url = require(src, "url", path, errors)
        require(src, "fact", path, errors)
        if sid in source_ids:
            err(errors, path + ".id", f"duplicate source id {sid!r}")
        if sid:
            source_ids.add(sid)
        if url and not valid_url(url):
            err(errors, path + ".url", f"invalid URL {url!r}")

    lines = ep.get("lines", [])
    if not isinstance(lines, list) or not lines:
        err(errors, "$.lines", "must be a non-empty array")
        lines = []
    expected_n = 1
    for i, line in enumerate(lines):
        path = f"$.lines[{i}]"
        if not isinstance(line, dict):
            err(errors, path, "line must be an object")
            continue
        n = require(line, "n", path, errors)
        speaker = require(line, "speaker", path, errors)
        text = require(line, "text", path, errors)
        if n != expected_n:
            err(errors, path + ".n", f"expected line number {expected_n}, got {n!r}")
        expected_n += 1
        if speaker not in SPEAKERS:
            err(errors, path + ".speaker", f"unknown speaker {speaker!r}")
        if not isinstance(text, str) or not text.strip():
            err(errors, path + ".text", "text must be a non-empty string")
        mood = line.get("mood", "neutral")
        if mood not in MOODS:
            err(errors, path + ".mood", f"unknown mood {mood!r}")
        move = line.get("move")
        if move is not None and move not in MOVES:
            err(errors, path + ".move", f"unknown move {move!r}")
        gesture = line.get("gesture")
        if gesture is not None and gesture not in rig_pose.POSES:
            err(errors, path + ".gesture", f"unknown gesture {gesture!r}")
        cites = line.get("cite", [])
        if not isinstance(cites, list):
            err(errors, path + ".cite", "cite must be an array")
            cites = []
        for cite in cites:
            if cite not in source_ids:
                err(errors, path + ".cite", f"unknown source id {cite!r}")
        for j, idx in enumerate(line.get("emphasis", [])):
            if not isinstance(idx, int) or idx < 0:
                err(errors, f"{path}.emphasis[{j}]", "must be a non-negative integer")
        if "screen" in line:
            validate_screen(line["screen"], path + ".screen", errors, base_dir)
        if "screens" in line:
            screens = line["screens"]
            if not isinstance(screens, list) or not screens:
                err(errors, path + ".screens", "screens must be a non-empty array")
            else:
                for j, item in enumerate(screens):
                    ipath = f"{path}.screens[{j}]"
                    if not isinstance(item, dict):
                        err(errors, ipath, "screen timeline item must be an object")
                        continue
                    if "at" in item and not isinstance(item["at"], (int, float)):
                        err(errors, ipath + ".at", "at must be a number of seconds")
                    if "start_word" in item and (not isinstance(item["start_word"], int) or item["start_word"] < 0):
                        err(errors, ipath + ".start_word", "start_word must be a non-negative integer")
                    spec = item.get("screen") if isinstance(item.get("screen"), dict) else item
                    validate_screen(spec, ipath + (".screen" if "screen" in item else ""), errors, base_dir)

    for key in ("intro_meme", "outro_meme", "background_meme"):
        if key not in ep:
            continue
        spec = ep[key]
        if not isinstance(spec, dict):
            err(errors, f"$.{key}", f"{key} must be an object")
            continue
        require(spec, "prompt", f"$.{key}", errors)
        path_val = require(spec, "path", f"$.{key}", errors)
        if path_val:
            image_path = Path(path_val).expanduser()
            if not image_path.is_absolute():
                image_path = base_dir / image_path
            if not image_path.exists():
                err(errors, f"$.{key}.path", f"image does not exist: {image_path}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_json")
    args = parser.parse_args()
    ep_path = Path(args.episode_json).resolve()
    ep = json.loads(ep_path.read_text())
    errors = validate_episode(ep, ep_path.parent)
    if errors:
        print("Episode validation failed:", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        sys.exit(1)
    print(f"ok: {ep_path}")


if __name__ == "__main__":
    main()
