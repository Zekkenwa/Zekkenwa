#!/usr/bin/env python3
"""Generate a beautiful MAL stats SVG card for GitHub profile README."""

import json
import urllib.request
import urllib.error
import sys
import time
import base64
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
    
    parts = [f'<rect x="{x}" y="{y}" width="{width}" height="8" rx="4" fill="{BAR_BG}"/>']
    # Clip path for rounded corners
    clip_id = f"clip-{y}-{x}"
    parts.append(f'<clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{width}" height="8" rx="4"/></clipPath>')
    parts.append(f'<g clip-path="url(#{clip_id})">')
    
    offset = 0
    for val, color in zip(values, colors):
        seg_width = (val / total) * width
        if seg_width > 0:
            parts.append(f'<rect x="{x + offset}" y="{y}" width="{seg_width}" height="8" fill="{color}"/>')
            offset += seg_width
    
    parts.append('</g>')
    return '\n    '.join(parts)


def make_stat_item(x, y, label, value, icon_emoji):
    """Generate a stat item with label and value."""
    return f'''<text x="{x}" y="{y}" fill="{TEXT_SECONDARY}" font-size="11" font-family="Segoe UI, Ubuntu, sans-serif">{icon_emoji} {label}</text>
    <text x="{x}" y="{y + 18}" fill="{TEXT_PRIMARY}" font-size="16" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">{value}</text>'''


def make_legend_item(x, y, color, label, count):
    """Generate a legend item for the progress bar."""
    return f'''<circle cx="{x + 4}" cy="{y}" r="4" fill="{color}"/>
    <text x="{x + 14}" y="{y + 4}" fill="{TEXT_SECONDARY}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif">{label} ({count})</text>'''


def generate_svg(stats, favorites, updates):
    """Generate the complete SVG card."""
    anime = stats["data"]["anime"]
    manga = stats["data"]["manga"]
    
    # Calculate totals for progress bars
    anime_total = anime["total_entries"]
    manga_total = manga["total_entries"]
    
    # Get top 5 favorite anime
    fav_anime = favorites.get("data", {}).get("favorites", {}).get("anime", [])[:5]
    
    # Get recent updates
    recent_anime = updates.get("data", {}).get("updates", {}).get("anime", [])[:3]
    
    # Card dimensions
    card_width = 480
    card_height = 520
    padding = 24
    content_width = card_width - (padding * 2)
    
    # Build SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}">
  <defs>
    <style>
      @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}
      .card {{ animation: fadeIn 0.6s ease-out; }}
      .stat-group {{ animation: fadeIn 0.6s ease-out backwards; }}
      .stat-group-1 {{ animation-delay: 0.1s; }}
      .stat-group-2 {{ animation-delay: 0.2s; }}
      .stat-group-3 {{ animation-delay: 0.3s; }}
      .stat-group-4 {{ animation-delay: 0.4s; }}
    </style>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{ACCENT};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{ACCENT};stop-opacity:0.05" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  
  <!-- Card background -->
  <rect width="{card_width}" height="{card_height}" rx="12" fill="{CARD_BG}" stroke="{BORDER_COLOR}" stroke-width="1" stroke-opacity="0.4" class="card"/>
  
  <!-- Header background -->
  <rect width="{card_width}" height="56" rx="12" fill="url(#headerGrad)"/>
  <rect y="12" width="{card_width}" height="44" fill="url(#headerGrad)"/>
  
  <!-- Header -->
  <g class="stat-group stat-group-1">
    <text x="{padding}" y="28" fill="{ACCENT_LIGHT}" font-size="11" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif" text-transform="uppercase" letter-spacing="1.5">MY ANIME LIST</text>
    <text x="{padding}" y="46" fill="{TEXT_PRIMARY}" font-size="16" font-weight="700" font-family="Segoe UI, Ubuntu, sans-serif">ðŸ“Š {MAL_USER}'s Stats</text>
    <text x="{card_width - padding}" y="38" fill="{TEXT_MUTED}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="end">myanimelist.net</text>
  </g>
  
  <!-- Divider -->
  <line x1="{padding}" y1="62" x2="{card_width - padding}" y2="62" stroke="{BORDER_COLOR}" stroke-opacity="0.2" stroke-width="1"/>
  
  <!-- Anime Stats Section -->
  <g class="stat-group stat-group-2">
    <text x="{padding}" y="84" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">ðŸŽ¬ ANIME</text>
    
    <!-- Stats row -->
    {make_stat_item(padding, 100, "Days Watched", f"{anime['days_watched']:.1f}", "â±")}
    {make_stat_item(padding + 110, 100, "Episodes", f"{anime['episodes_watched']:,}", "â–¶")}
    {make_stat_item(padding + 220, 100, "Mean Score", f"{anime['mean_score']:.2f}", "â­")}
    {make_stat_item(padding + 330, 100, "Entries", f"{anime_total}", "ðŸ“‹")}
    
    <!-- Progress bar -->
    {make_progress_bar(padding, 142, content_width, 
        [anime['watching'], anime['completed'], anime['on_hold'], anime['dropped'], anime['plan_to_watch']],
        [WATCHING_COLOR, COMPLETED_COLOR, ON_HOLD_COLOR, DROPPED_COLOR, PLAN_COLOR],
        anime_total)}
    
    <!-- Legend -->
    {make_legend_item(padding, 162, WATCHING_COLOR, "Watching", anime['watching'])}
    {make_legend_item(padding + 100, 162, COMPLETED_COLOR, "Completed", anime['completed'])}
    {make_legend_item(padding + 210, 162, ON_HOLD_COLOR, "On Hold", anime['on_hold'])}
    {make_legend_item(padding + 310, 162, DROPPED_COLOR, "Dropped", anime['dropped'])}
    {make_legend_item(padding + 395, 162, PLAN_COLOR, "PTW", anime['plan_to_watch'])}
  </g>
  
  <!-- Divider -->
  <line x1="{padding}" y1="180" x2="{card_width - padding}" y2="180" stroke="{BORDER_COLOR}" stroke-opacity="0.15" stroke-width="1"/>
  
  <!-- Manga Stats Section -->
  <g class="stat-group stat-group-3">
    <text x="{padding}" y="202" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">ðŸ“– MANGA</text>
    
    {make_stat_item(padding, 218, "Days Read", f"{manga['days_read']:.1f}", "â±")}
    {make_stat_item(padding + 110, 218, "Chapters", f"{manga['chapters_read']:,}", "ðŸ“„")}
    {make_stat_item(padding + 220, 218, "Volumes", f"{manga['volumes_read']}", "ðŸ“š")}
    {make_stat_item(padding + 330, 218, "Entries", f"{manga_total}", "ðŸ“‹")}
    
    <!-- Manga progress bar -->
    {make_progress_bar(padding, 260, content_width,
        [manga['reading'], manga['completed'], manga['on_hold'], manga['dropped'], manga['plan_to_read']],
        [WATCHING_COLOR, COMPLETED_COLOR, ON_HOLD_COLOR, DROPPED_COLOR, PLAN_COLOR],
        manga_total)}
    
    <!-- Legend -->
    {make_legend_item(padding, 280, WATCHING_COLOR, "Reading", manga['reading'])}
    {make_legend_item(padding + 100, 280, COMPLETED_COLOR, "Completed", manga['completed'])}
    {make_legend_item(padding + 210, 280, ON_HOLD_COLOR, "On Hold", manga['on_hold'])}
    {make_legend_item(padding + 310, 280, DROPPED_COLOR, "Dropped", manga['dropped'])}
    {make_legend_item(padding + 395, 280, PLAN_COLOR, "PTR", manga['plan_to_read'])}
  </g>
  
  <!-- Divider -->
  <line x1="{padding}" y1="298" x2="{card_width - padding}" y2="298" stroke="{BORDER_COLOR}" stroke-opacity="0.15" stroke-width="1"/>
  
  <!-- Favorites Section -->
  <g class="stat-group stat-group-4">
    <text x="{padding}" y="320" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">â¤ FAVORITE ANIME</text>'''
    
    # Add favorite anime titles
    fav_y = 340
    for i, fav in enumerate(fav_anime[:5]):
        title = fav.get("title", "Unknown")
        # Truncate long titles
        if len(title) > 50:
            title = title[:47] + "..."
        fav_type = fav.get("type", "")
        year = fav.get("start_year", "")
        
        svg += f'''
    <circle cx="{padding + 4}" cy="{fav_y + i * 22}" r="3" fill="{ACCENT}"/>
    <text x="{padding + 14}" y="{fav_y + 4 + i * 22}" fill="{TEXT_PRIMARY}" font-size="11" font-family="Segoe UI, Ubuntu, sans-serif">{title}</text>
    <text x="{card_width - padding}" y="{fav_y + 4 + i * 22}" fill="{TEXT_MUTED}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="end">{fav_type} Â· {year}</text>'''
    
    svg += f'''
  </g>
  
  <!-- Divider -->
  <line x1="{padding}" y1="456" x2="{card_width - padding}" y2="456" stroke="{BORDER_COLOR}" stroke-opacity="0.15" stroke-width="1"/>
  
  <!-- Recently Watched -->
  <g class="stat-group stat-group-4">
    <text x="{padding}" y="476" fill="{ACCENT_LIGHT}" font-size="12" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif">ðŸ• RECENTLY UPDATED</text>'''
    
    recent_y = 494
    for i, update in enumerate(recent_anime[:2]):
        title = update.get("entry", {}).get("title", "Unknown")
        if len(title) > 40:
            title = title[:37] + "..."
        score = update.get("score", 0)
        status = update.get("status", "")
        score_text = f"â˜… {score}" if score > 0 else status
        
        svg += f'''
    <text x="{padding + 8}" y="{recent_y + i * 18}" fill="{TEXT_SECONDARY}" font-size="10" font-family="Segoe UI, Ubuntu, sans-serif">â–¸ {title}</text>
    <text x="{card_width - padding}" y="{recent_y + i * 18}" fill="{ACCENT}" font-size="10" font-weight="600" font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="end">{score_text}</text>'''
    
    svg += '''
  </g>
</svg>'''
    
    return svg


def main():
    print("ðŸŽŒ Fetching MAL stats...")
    stats = fetch_json(f"/users/{MAL_USER}/statistics")
    
    print("â¤ Fetching favorites...")
    time.sleep(1)  # Rate limit courtesy
    favorites = fetch_json(f"/users/{MAL_USER}/full")
    
    print("ðŸ• Fetching recent updates...")
    time.sleep(1)
    # The /full endpoint already has updates, reuse it
    updates = {"data": favorites.get("data", {})}
    
    print("ðŸŽ¨ Generating SVG card...")
    svg = generate_svg(stats, favorites, updates)
    
    output_path = os.environ.get("OUTPUT_PATH", "mal-stats.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    
    print(f"âœ… SVG card saved to {output_path}")
    
    # Also output stats as env vars for README update
    anime = stats["data"]["anime"]
    manga = stats["data"]["manga"]
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"anime_days={anime['days_watched']}\n")
            f.write(f"manga_days={manga['days_read']}\n")
            f.write(f"mean_score={anime['mean_score']}\n")
            f.write(f"total_entries={anime['total_entries'] + manga['total_entries']}\n")


if __name__ == "__main__":
    main()
