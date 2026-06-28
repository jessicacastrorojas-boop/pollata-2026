#!/usr/bin/env python3
"""
update_scores.py
Fetches completed World Cup 2026 match results from ESPN API and
updates the result[] arrays in index.html.
Runs via GitHub Actions every 30 minutes.
"""

import re
import json
import urllib.request
from datetime import date, timedelta

# ── Team name mapping: ESPN English → Spanish used in MATCHES ──────────────
TEAM_MAP = {
    'South Africa':                'Sudáfrica',
    'Canada':                      'Canadá',
    'Germany':                     'Alemania',
    'Paraguay':                    'Paraguay',
    'Netherlands':                 'Países Bajos',
    'Morocco':                     'Marruecos',
    'Brazil':                      'Brasil',
    'Japan':                       'Japón',
    'France':                      'Francia',
    'Sweden':                      'Suecia',
    'Ivory Coast':                 'Costa de Marfil',
    "Côte d'Ivoire":               'Costa de Marfil',
    'Norway':                      'Noruega',
    'Mexico':                      'México',
    'Ecuador':                     'Ecuador',
    'England':                     'Inglaterra',
    'DR Congo':                    'R. del Congo',
    'Congo DR':                    'R. del Congo',
    'Democratic Republic of Congo':'R. del Congo',
    'United States':               'Estados Unidos',
    'USA':                         'Estados Unidos',
    'Bosnia and Herzegovina':      'Bosnia y Herzegovina',
    'Bosnia & Herzegovina':        'Bosnia y Herzegovina',
    'Belgium':                     'Bélgica',
    'Senegal':                     'Senegal',
    'Portugal':                    'Portugal',
    'Croatia':                     'Croacia',
    'Spain':                       'España',
    'Austria':                     'Austria',
    'Switzerland':                 'Suiza',
    'Algeria':                     'Argelia',
    'Argentina':                   'Argentina',
    'Cape Verde':                  'Cabo Verde',
    'Colombia':                    'Colombia',
    'Ghana':                       'Ghana',
    'Australia':                   'Australia',
    'Egypt':                       'Egipto',
    # Knockout rounds (just in case)
    'Uruguay':                     'Uruguay',
    'Korea Republic':              'Corea del Sur',
    'United States':               'Estados Unidos',
}

ESPN_URL = (
    'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard'
)


def fetch_completed(date_str: str) -> list[tuple]:
    """Return list of (home_es, away_es, home_score, away_score) for completed matches."""
    url = f'{ESPN_URL}?dates={date_str}'
    req = urllib.request.Request(url, headers={'User-Agent': 'pollata-bot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except Exception as exc:
        print(f'  ⚠ Could not fetch {date_str}: {exc}')
        return []

    results = []
    for event in data.get('events', []):
        comp = event['competitions'][0]
        if not comp['status']['type']['completed']:
            continue  # match not finished yet

        competitors = comp['competitors']
        home = next((c for c in competitors if c['homeAway'] == 'home'), None)
        away = next((c for c in competitors if c['homeAway'] == 'away'), None)
        if not home or not away:
            continue

        home_en = home['team']['displayName']
        away_en = away['team']['displayName']
        home_es = TEAM_MAP.get(home_en, home_en)
        away_es = TEAM_MAP.get(away_en, away_en)
        home_sc = int(float(home['score']))
        away_sc = int(float(away['score']))

        results.append((home_es, away_es, home_sc, away_sc))
        print(f'  ✓ {home_es} {home_sc}–{away_sc} {away_es}')
    return results


def update_html(matches: list[tuple], path: str = 'index.html') -> int:
    """
    For each completed match, update the result:[null,null] entry in index.html.
    Only replaces entries that are still null (never overwrites an already-set result).
    Returns number of updated matches.
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = 0
    for home_es, away_es, score_home, score_away in matches:
        # Try both team orderings (our file may list them as home or away first)
        for t1, t2, s1, s2 in [
            (home_es, away_es, score_home, score_away),
            (away_es, home_es, score_away, score_home),
        ]:
            # Match the specific MATCHES entry: team1 … team2 … result:[null,null]
            pattern = (
                r"(team1\s*:\s*['\"]" + re.escape(t1) + r"['\"]"
                r".{0,200}?"
                r"team2\s*:\s*['\"]" + re.escape(t2) + r"['\"]"
                r".{0,200}?"
                r"result\s*:\s*\[)\s*null\s*,\s*null\s*(\])"
            )
            new_content, n = re.subn(
                pattern,
                rf'\g<1>{s1},{s2}\2',
                content,
                flags=re.DOTALL,
            )
            if n:
                content = new_content
                changes += 1
                print(f'  ✏ Updated result: {t1} {s1}–{s2} {t2}')
                break  # found the right ordering, no need to try the other

    if changes:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'\n✅ {changes} match(es) updated in {path}')
    else:
        print('\n— No pending results to update —')

    return changes


def main():
    print('=== Pollata 2026 — Score Updater ===')

    # Date range: Round of 32 (Jun 28 – Jul 3) + buffer
    start = date(2026, 6, 28)
    end   = date(2026, 7, 4)

    all_results: list[tuple] = []
    d = start
    while d <= end:
        ds = d.strftime('%Y%m%d')
        print(f'\nFetching {ds}…')
        results = fetch_completed(ds)
        all_results.extend(results)
        d += timedelta(days=1)

    print(f'\nTotal completed matches found: {len(all_results)}')

    if all_results:
        update_html(all_results)
    else:
        print('Nothing to update.')


if __name__ == '__main__':
    main()
