#!/usr/bin/env python3
"""Generate a beautiful MAL stats SVG card for GitHub profile README."""

import json
import urllib.request
import urllib.error
import sys
import time
import os

JIKAN_BASE = "https://api.jikan.moe/v4"
MAL_USER = os.environ.get("MAL_USER", "RFA-Chan")
MAX_RETRIES = 5
RETRY_DELAY = 10

# Theme colors
BG_COLOR = "#0d1117"
CARD_BG = "#161b22"
BORDER_COLOR = "#458B73"
ACCENT = "#458B73"
ACCENT_LIGHT = "#5aab8f"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED = "#6e7681"
BAR_BG = "#21262d"

# Stat colors
WATCHING_COLOR = "#458B73"
COMPLETED_COLOR = "#3fb950"
ON_HOLD_COLOR = "#d29922"
DROPPED_COLOR = "#f85149"
PLAN_COLOR = "#6e7681"


def fetch_json(endpoint):
    """Fetch JSON from Jikan API with retry logic."""
    url = f"{JIKAN_BASE}{endpoint}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  Attempt {attempt}/{MAX_RETRIES}: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Actions-MAL-Card/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = RETRY_DELAY * attempt * 2
                print(f"  Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
            elif e.code in (500, 502, 503, 504):
                wait = RETRY_DELAY * attempt
                print(f"  Server error ({e.code}). Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  HTTP Error {e.code}")
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"  Error: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_DELAY * attempt)
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts")


def make_progress_bar(x, y, width, values, colors, total):
    """Generate an SVG progress bar with multiple segments."""
    if total == 0:
        return f'<rect x="{x}" y="{y}" width="{width}" height="8" rx="4" fill="{BAR_BG}"/>'

    clip_id = f"clip-{y}-{x}"
    parts = [
        f'<rect x="{x}" y="{y}" width="{width}" height="8" rx="4" fill="{BAR_BG}"/>',
        f'<clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{width}" height="8" rx="4"/></clipPath>',
        f'<g clip-path="url(#{clip_id})">'
    ]

    offset = 0
    for val, color in zip(values, colors):
        seg_width = (val / total) * width
        if seg_width > 0:
            parts.append(f'<rect x="{x + offset}" y="{y}" width="{seg_width}" height="8" fill="{color}"/>')
            offset += seg_width

    parts.append('</g>')
    return '\n    '.join(parts)


def make_stat_item(x, y, label, value):
    """Generate a stat item with label and value."""
    return f'''<text x="{x}" y="{y}" fill="{TEXT_SECONDARY}" font-size="11" font-family="Segoe UI, Ubuntu, sans-serif">{label}</text>
    <text x="{x}" y="{y + 18}" fill="{TEXT_PRIMARY}" font-size="16" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">{value}</text>'''


def make_legend_item(x, y, color, label, count):
    """Generate a legend item for the progress bar."""
    return f'''<circle cx="{x + 4}" cy="{y}" r="4" fill="{color}"/>
    <text x="{x + 14}" y="{y + 4}" fill="{TEXT_SECONDARY}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif">{label} ({count})</text>'''


def escape_xml(text):
    """Escape special XML characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")


def generate_svg(stats, favorites, updates):
    """Generate the complete SVG card."""
    anime = stats["data"]["anime"]
    manga = stats["data"]["manga"]

    anime_total = anime["total_entries"]
    manga_total = manga["total_entries"]

    fav_anime = favorites.get("data", {}).get("favorites", {}).get("anime", [])[:5]
    recent_anime = favorites.get("data", {}).get("updates", {}).get("anime", [])[:2]

    card_width = 480
    card_height = 520
    padding = 24
    content_width = card_width - (padding * 2)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}">
  <defs>
    <style>
      @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}
      .card {{ animation: fadeIn 0.6s ease-out; }}
      .stat-group {{ animation: fadeIn 0.6s ease-out backwards; }}
      .delay-1 {{ animation-delay: 0.1s; }}
      .delay-2 {{ animation-delay: 0.2s; }}
      .delay-3 {{ animation-delay: 0.3s; }}
      .delay-4 {{ animation-delay: 0.4s; }}
    </style>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{ACCENT};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{ACCENT};stop-opacity:0.05" />
    </linearGradient>
  </defs>

  <!-- Card background -->
  <rect width="{card_width}" height="{card_height}" rx="12" fill="{CARD_BG}" stroke="{BORDER_COLOR}" stroke-width="1" stroke-opacity="0.4" class="card"/>

  <!-- Header background -->
  <rect width="{card_width}" height="56" rx="12" fill="url(#headerGrad)"/>
  <rect y="12" width="{card_width}" height="44" fill="url(#headerGrad)"/>

  <!-- Header -->
  <g class="stat-group delay-1">
    <text x="{padding}" y="28" fill="{ACCENT_LIGHT}" font-size="11" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif" letter-spacing="1.5">MY ANIME LIST</text>
    <text x="{padding}" y="46" fill="{TEXT_PRIMARY}" font-size="16" font-weight="700" font-family="Segoe UI, Ubuntu, sans-serif">{escape_xml(MAL_USER)}&apos;s Stats</text>
    <text x="{card_width - padding}" y="38" fill="{TEXT_MUTED}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="end">myanimelist.net</text>
  </g>

  <!-- Divider -->
  <line x1="{padding}" y1="62" x2="{card_width - padding}" y2="62" stroke="{BORDER_COLOR}" stroke-opacity="0.2" stroke-width="1"/>

  <!-- Anime Stats Section -->
  <g class="stat-group delay-2">
    <text x="{padding}" y="84" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">ANIME</text>

    {make_stat_item(padding, 100, "Days Watched", f"{anime['days_watched']:.1f}")}
    {make_stat_item(padding + 110, 100, "Episodes", f"{anime['episodes_watched']:,}")}
    {make_stat_item(padding + 220, 100, "Mean Score", f"{anime['mean_score']:.2f}")}
    {make_stat_item(padding + 330, 100, "Entries", f"{anime_total}")}

    {make_progress_bar(padding, 142, content_width,
        [anime['watching'], anime['completed'], anime['on_hold'], anime['dropped'], anime['plan_to_watch']],
        [WATCHING_COLOR, COMPLETED_COLOR, ON_HOLD_COLOR, DROPPED_COLOR, PLAN_COLOR],
        anime_total)}

    {make_legend_item(padding, 162, WATCHING_COLOR, "Watching", anime['watching'])}
    {make_legend_item(padding + 100, 162, COMPLETED_COLOR, "Completed", anime['completed'])}
    {make_legend_item(padding + 215, 162, ON_HOLD_COLOR, "On Hold", anime['on_hold'])}
    {make_legend_item(padding + 310, 162, DROPPED_COLOR, "Dropped", anime['dropped'])}
    {make_legend_item(padding + 400, 162, PLAN_COLOR, "PTW", anime['plan_to_watch'])}
  </g>

  <!-- Divider -->
  <line x1="{padding}" y1="180" x2="{card_width - padding}" y2="180" stroke="{BORDER_COLOR}" stroke-opacity="0.15" stroke-width="1"/>

  <!-- Manga Stats Section -->
  <g class="stat-group delay-3">
    <text x="{padding}" y="202" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">MANGA</text>

    {make_stat_item(padding, 218, "Days Read", f"{manga['days_read']:.1f}")}
    {make_stat_item(padding + 110, 218, "Chapters", f"{manga['chapters_read']:,}")}
    {make_stat_item(padding + 220, 218, "Volumes", f"{manga['volumes_read']}")}
    {make_stat_item(padding + 330, 218, "Entries", f"{manga_total}")}

    {make_progress_bar(padding, 260, content_width,
        [manga['reading'], manga['completed'], manga['on_hold'], manga['dropped'], manga['plan_to_read']],
        [WATCHING_COLOR, COMPLETED_COLOR, ON_HOLD_COLOR, DROPPED_COLOR, PLAN_COLOR],
        manga_total)}

    {make_legend_item(padding, 280, WATCHING_COLOR, "Reading", manga['reading'])}
    {make_legend_item(padding + 100, 280, COMPLETED_COLOR, "Completed", manga['completed'])}
    {make_legend_item(padding + 215, 280, ON_HOLD_COLOR, "On Hold", manga['on_hold'])}
    {make_legend_item(padding + 310, 280, DROPPED_COLOR, "Dropped", manga['dropped'])}
    {make_legend_item(padding + 400, 280, PLAN_COLOR, "PTR", manga['plan_to_read'])}
  </g>

  <!-- Divider -->
  <line x1="{padding}" y1="298" x2="{card_width - padding}" y2="298" stroke="{BORDER_COLOR}" stroke-opacity="0.15" stroke-width="1"/>

  <!-- Favorites Section -->
  <g class="stat-group delay-4">
    <text x="{padding}" y="320" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">FAVORITE ANIME</text>'''

    fav_y = 340
    for i, fav in enumerate(fav_anime[:5]):
        title = escape_xml(fav.get("title", "Unknown"))
        if len(title) > 50:
            title = title[:47] + "..."
        fav_type = escape_xml(fav.get("type", ""))
        year = fav.get("start_year", "")

        svg += f'''
    <circle cx="{padding + 4}" cy="{fav_y + i * 22}" r="3" fill="{ACCENT}"/>
    <text x="{padding + 14}" y="{fav_y + 4 + i * 22}" fill="{TEXT_PRIMARY}" font-size="11" font-family="Segoe UI, Ubuntu, sans-serif">{title}</text>
    <text x="{card_width - padding}" y="{fav_y + 4 + i * 22}" fill="{TEXT_MUTED}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="end">{fav_type} / {year}</text>'''

    svg += f'''
  </g>

  <!-- Divider -->
  <line x1="{padding}" y1="456" x2="{card_width - padding}" y2="456" stroke="{BORDER_COLOR}" stroke-opacity="0.15" stroke-width="1"/>

  <!-- Recently Watched -->
  <g class="stat-group delay-4">
    <text x="{padding}" y="476" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">RECENTLY UPDATED</text>'''

    for i, update in enumerate(recent_anime[:2]):
        title = escape_xml(update.get("entry", {}).get("title", "Unknown"))
        if len(title) > 42:
            title = title[:39] + "..."
        score = update.get("score", 0)
        status = escape_xml(update.get("status", ""))
        score_text = f"Score: {score}" if score > 0 else status

        svg += f'''
    <text x="{padding + 8}" y="{494 + i * 18}" fill="{TEXT_SECONDARY}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif">&gt; {title}</text>
    <text x="{card_width - padding}" y="{494 + i * 18}" fill="{ACCENT}" font-size="10" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="end">{score_text}</text>'''

    svg += '''
  </g>
</svg>'''

    return svg


def main():
    print("Fetching MAL stats...")
    stats = fetch_json(f"/users/{MAL_USER}/statistics")

    print("Fetching full profile (favorites + updates)...")
    time.sleep(1)
    full = fetch_json(f"/users/{MAL_USER}/full")

    print("Generating SVG card...")
    svg = generate_svg(stats, full, None)

    output_path = os.environ.get("OUTPUT_PATH", "mal-stats.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Done! SVG card saved to {output_path}")


if __name__ == "__main__":
    main()
