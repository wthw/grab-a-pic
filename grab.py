#!/usr/bin/env python3
"""Grab the default (color) team photo for a surname from liberated.school/team.

Each team-member card on the page holds two background images stacked on top of
each other that swap on mouse hover (a Tilda "t857" block). The relevant CSS is:

    .t857__bgimg_first_hover                         -> opacity 1   (default)
    .t857__bgimg_second                              -> opacity 0   (default)
    .t857__imgwrapper:hover .t857__bgimg_first_hover -> opacity 0   (on hover)
    .t857__imgwrapper:hover .t857__bgimg_second      -> opacity 1   (on hover)

So the image shown when the pointer is NOT hovering -- the colour portrait we
want -- carries the class ``t857__bgimg_first_hover``. The childhood black &
white photo that appears on hover carries ``t857__bgimg_second``.

This script picks the default-visible image by that class and, as a safety net,
verifies it is the more colourful of the two (the "catch" the task warns about).
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageStat

TEAM_URL = "https://liberated.school/team"
DEFAULT_CLASS = "t857__bgimg_first_hover"  # shown when NOT hovering (colour)
HOVER_CLASS = "t857__bgimg_second"         # shown on hover (b/w childhood photo)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def fetch_page(local: str | None) -> str:
    """Return the team page HTML, from a local file if given, else over HTTP."""
    if local:
        return Path(local).read_text(encoding="utf-8")
    resp = requests.get(TEAM_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def card_text(card) -> str:
    """Human-readable name for a card (subtitle + title), used for matching."""
    parts: list[str] = []
    for el in card.select('[field^="li_subtitle"], [field^="li_title"]'):
        text = el.get_text(" ", strip=True)
        if text:
            parts.append(text)
    return " ".join(parts)


def card_image(card, hover: bool) -> str | None:
    """Return the full-resolution image URL for a card.

    ``data-original`` holds the real (lazy-loaded) image; the inline
    ``background-image`` is only a tiny 20px placeholder, so it is ignored.
    """
    cls = HOVER_CLASS if hover else DEFAULT_CLASS
    div = card.select_one(f"div.{cls}")
    if not div:
        return None
    url = div.get("data-original")
    if not url:
        meta = div.select_one('meta[itemprop="image"]')
        url = meta.get("content") if meta else None
    return url


def iter_cards(soup: BeautifulSoup):
    return soup.select("li.t857__col")


def colourfulness(image_bytes: bytes) -> float:
    """Mean HSV saturation; ~0 for grayscale, higher for a colour photo."""
    im = Image.open(io.BytesIO(image_bytes))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    saturation = im.convert("RGB").convert("HSV").getchannel("S")
    return ImageStat.Stat(saturation).mean[0]


def ext_from_url(url: str) -> str:
    suffix = Path(unquote(urlparse(url).path)).suffix.lower()
    return suffix or ".jpg"


def download(url: str) -> bytes:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.content


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Save the default colour team photo for a surname from "
        "liberated.school/team (not the b/w hover photo).",
    )
    parser.add_argument(
        "surname",
        nargs="?",
        help="Surname to look up, e.g. Тобенгауз (case-insensitive substring).",
    )
    parser.add_argument(
        "-o", "--outdir", default=".", help="Directory to save into (default: .)."
    )
    parser.add_argument(
        "--page", help="Read HTML from a local file instead of fetching the site."
    )
    parser.add_argument(
        "--list", action="store_true", help="List all team members and exit."
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the colour sanity check on the chosen image.",
    )
    args = parser.parse_args()

    soup = BeautifulSoup(fetch_page(args.page), "lxml")
    cards = iter_cards(soup)
    if not cards:
        print("No team cards found on the page.", file=sys.stderr)
        return 1

    if args.list:
        for card in cards:
            print(card_text(card))
        return 0

    if not args.surname:
        parser.error("a surname is required (or use --list)")

    needle = args.surname.casefold()
    matches = [c for c in cards if needle in card_text(c).casefold()]
    if not matches:
        print(f"No team member matching {args.surname!r}.", file=sys.stderr)
        print("Try --list to see all names.", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"{len(matches)} matches for {args.surname!r}:", file=sys.stderr)
        for c in matches:
            print(f"  - {card_text(c)}", file=sys.stderr)
        print("Use a more specific surname.", file=sys.stderr)
        return 1

    card = matches[0]
    name = card_text(card)
    default_url = card_image(card, hover=False)
    if not default_url:
        print(f"Could not find the default image for {name!r}.", file=sys.stderr)
        return 1

    chosen_url = default_url
    if not args.no_verify:
        hover_url = card_image(card, hover=True)
        default_img = download(default_url)
        if hover_url and hover_url != default_url:
            hover_img = download(hover_url)
            c_default = colourfulness(default_img)
            c_hover = colourfulness(hover_img)
            print(
                f"Colour check: default={c_default:.1f}  hover={c_hover:.1f} "
                f"(higher = more colourful)",
                file=sys.stderr,
            )
            if c_hover > c_default:
                print(
                    "Warning: the hover image looks more colourful; the page "
                    "layout may have changed. Keeping the default-visible image "
                    "as requested.",
                    file=sys.stderr,
                )
        data = default_img
    else:
        data = download(chosen_url)

    out_path = Path(args.outdir) / f"{args.surname}{ext_from_url(chosen_url)}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print(f"Saved {name} -> {out_path} ({len(data):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
