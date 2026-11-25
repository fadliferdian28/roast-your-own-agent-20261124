#!/usr/bin/env python3
"""Validate entry.txt and copy it byte-for-byte into the output directory."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path


MAX_CHARACTERS = 200
SOURCE_NAME = "entry.txt"


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_and_validate(source: Path) -> str:
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read {source}: {exc}") from exc

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{source} is not valid UTF-8: {exc}") from exc

    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith("\n") or text.endswith("\r"):
        text = text[:-1]

    if not text.strip():
        raise ValueError(f"{source} is empty or whitespace-only")
    if len(text) > MAX_CHARACTERS:
        raise ValueError(
            f"{source} has {len(text)} characters; maximum is {MAX_CHARACTERS}"
        )
    if "\n" in text or "\r" in text:
        raise ValueError(f"{source} must contain exactly one line")
    return text


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    source = script_dir / SOURCE_NAME

    try:
        text = load_and_validate(source)
    except ValueError as exc:
        return fail(str(exc))

    output_root = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    destination = Path(output_root).expanduser() / SOURCE_NAME

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return fail(f"cannot create output directory {destination.parent}: {exc}")

    try:
        if destination.exists() and os.path.samefile(source, destination):
            return fail(f"source and destination are the same file: {source}")
    except OSError as exc:
        return fail(f"cannot compare source and destination: {exc}")

    try:
        shutil.copyfile(source, destination)
    except shutil.SameFileError:
        return fail(f"source and destination are the same file: {source}")
    except OSError as exc:
        return fail(f"cannot copy {source} to {destination}: {exc}")

    source_hash = sha256(source)
    destination_hash = sha256(destination)
    if source_hash != destination_hash:
        try:
            destination.unlink()
        except OSError:
            pass
        return fail(
            "copy verification failed: "
            f"source sha256={source_hash}, destination sha256={destination_hash}"
        )

    print(f"copied {source} -> {destination}")
    print(f"characters: {len(text)}")
    print(f"sha256: {source_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
