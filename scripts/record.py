#!/usr/bin/env python3
"""Draws assets/record.svg: an animated, isometric "Record of Deeds" of the last year's contributions.

    python scripts/record.py            (inside the GitHub Action: uses GITHUB_TOKEN and USERNAME)
    python scripts/record.py --demo     (made-up data, to look at the design on your own PC)
    python scripts/record.py --demo-sparse
"""
import base64
import datetime
import json
import math
import os
import random
import sys
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'record.svg')
W, H = 1200, 620
FONT = "'EB Garamond','Cormorant Garamond',Garamond,'Palatino Linotype','Book Antiqua',Georgia,serif"
BONE, DIM, GOLD, BLOOD = '#e2dacc', '#8f877c', '#b0945c', '#a8161a'

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
  }
}
"""
LEVELS = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}


def fetch(login, token):
    body = json.dumps({'query': QUERY, 'variables': {'login': login}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body,
                                 headers={'Authorization': 'bearer ' + token, 'User-Agent': 'profile-record'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get('errors'):
        raise SystemExit('GitHub said: ' + json.dumps(data['errors']))
    user = data['data']['user']
    weeks = [[(d['date'], d['contributionCount'], LEVELS.get(d['contributionLevel'], 0))
              for d in w['contributionDays']]
             for w in user['contributionsCollection']['contributionCalendar']['weeks']]
    langs = {}
    for repo in user['repositories']['nodes']:
        for e in repo['languages']['edges']:
            langs[e['node']['name']] = langs.get(e['node']['name'], 0) + e['size']
    return weeks, langs


def demo(sparse):
    random.seed(11)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 1 + 52 * 7) if today.weekday() != 6 \
        else today - datetime.timedelta(days=52 * 7)
    weeks, day = [], start
    while day <= today:
        week = []
        for _ in range(7):
            if day > today:
                break
            if sparse:
                c = random.choice([0, 0, 1, 2, 5]) if (today - day).days < 12 else 0
            else:
                mood = 0.5 + 0.5 * math.sin((day - start).days / 23.0)
                c = 0 if random.random() > 0.35 + 0.5 * mood else int(random.expovariate(1 / (2 + 9 * mood)))
            week.append((day.isoformat(), c, 0))
            day += datetime.timedelta(days=1)
        weeks.append(week)
    top = max((c for w in weeks for _, c, _ in w), default=0) or 1
    weeks = [[(d, c, 0 if c == 0 else min(4, 1 + int(3.999 * c / top))) for d, c, _ in w] for w in weeks]
    return weeks, {'C++': 820, 'Python': 140, 'PowerShell': 40}


def streaks(days):
    longest = cur = 0
    for _, c, _ in days:
        cur = cur + 1 if c else 0
        longest = max(longest, cur)
    tail = days[:-1] if days and days[-1][1] == 0 else days    # today may still be empty
    current = 0
    for _, c, _ in reversed(tail):
        if not c:
            break
        current += 1
    return current, longest


def poly(points, **attrs):
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    extra = ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<polygon points="{pts}"{extra}/>'


def text(x, y, s, size, fill, anchor='start', spacing=0, style='', extra=''):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'letter-spacing="{spacing}"{" font-style=\"italic\"" if style == "i" else ""}{extra}>{s}</text>')


def build(weeks, langs):
    days = [d for w in weeks for d in w]
    total = sum(c for _, c, _ in days)
    top = max((c for _, c, _ in days), default=0)
    current, longest = streaks(days)
    random.seed(3)
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      f'role="img" aria-label="The Record of Deeds: {total} contributions in the last year" font-family="{FONT}">')
    a('''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#030305"/><stop offset="0.6" stop-color="#0a0406"/><stop offset="1" stop-color="#1c0608"/></linearGradient>
<radialGradient id="moon" cx="0.42" cy="0.4" r="0.62"><stop offset="0" stop-color="#d8442e"/><stop offset="0.5" stop-color="#8f1216"/><stop offset="1" stop-color="#3a0507"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#a8161a" stop-opacity="0.5"/><stop offset="0.55" stop-color="#6d0c10" stop-opacity="0.14"/><stop offset="1" stop-color="#6d0c10" stop-opacity="0"/></radialGradient>
<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#b0945c" stop-opacity="0"/><stop offset="0.5" stop-color="#b0945c"/><stop offset="1" stop-color="#b0945c" stop-opacity="0"/></linearGradient>
<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5a0a0e"/><stop offset="1" stop-color="#d4302a"/></linearGradient>
<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff9a5a" stop-opacity="0"/><stop offset="0.5" stop-color="#ff9a5a" stop-opacity="0.3"/><stop offset="1" stop-color="#ff9a5a" stop-opacity="0"/></linearGradient>
<filter id="soft"><feGaussianBlur stdDeviation="28"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/></filter>
<clipPath id="frame"><rect width="1200" height="620"/></clipPath>
</defs>''')
    a(f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="url(#bg)"/>')
    # blood moon, low and large behind the far end of the road
    a('<circle cx="1010" cy="150" r="300" fill="url(#halo)"><animate attributeName="r" values="290;325;290" dur="10s" repeatCount="indefinite"/></circle>')
    moon = os.path.join(os.path.dirname(OUT), 'moon.jpg')
    if os.path.exists(moon):
        # the real blood moon (a photo, drawn into the picture so GitHub shows it)
        with open(moon, 'rb') as f:
            data = base64.b64encode(f.read()).decode()
        a(f'<image x="820" y="-40" width="380" height="380" href="data:image/jpeg;base64,{data}" '
          'style="mix-blend-mode:screen" opacity="0.92"><animate attributeName="opacity" values="0.92;0.74;0.92" '
          'dur="10s" repeatCount="indefinite"/></image>')
    else:
        a('<circle cx="1010" cy="150" r="104" fill="url(#moon)" opacity="0.5"/>')

    # ---- the isometric road of days
    hw, hh = 9.5, 4.75
    ox, oy = 62 + 7 * hw, 196
    cells = []
    for wi, week in enumerate(weeks):
        for date, count, level in week:
            di = (datetime.date.fromisoformat(date).weekday() + 1) % 7      # Sunday first
            cells.append((wi + di, wi, di, date, count, level))
    cells.sort()
    faces = {1: ('#6e1216', '#35080b', '#4e0a0e'), 2: ('#9e1a1c', '#4a0a0d', '#6c0e11'),
             3: ('#d4302a', '#64100f', '#901613'), 4: ('#ff7a3c', '#7c1710', '#b3261a')}
    g = hw - 0.7
    gh = hh - 0.35
    floor, towers = [], []
    for _, wi, di, date, count, level in cells:
        cx = ox + (wi - di) * hw
        cy = oy + (wi + di) * hh
        shade = random.choice(['#110a0d', '#130b0e', '#0f090c', '#150b0f'])
        floor.append(poly([(cx, cy - gh), (cx + g, cy), (cx, cy + gh), (cx - g, cy)], fill=shade,
                          stroke='#2a070b', stroke_width='0.6'))
        if not count:
            continue
        h = 6 + 40 * math.log1p(count) / math.log1p(max(top, 2))
        topc, left, right = faces[max(1, level)]
        begin = f'{0.25 + wi * 0.028 + di * 0.02:.2f}s'
        t = [f'<g opacity="0"><title>{date}: {count}</title>',
             f'<animate attributeName="opacity" from="0" to="1" begin="{begin}" dur="0.5s" fill="freeze"/>',
             f'<animateTransform attributeName="transform" type="translate" from="0 {h:.1f}" to="0 0" begin="{begin}" '
             f'dur="0.9s" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1" fill="freeze"/>',
             poly([(cx - g, cy - h), (cx, cy + gh - h), (cx, cy + gh), (cx - g, cy)], fill=left),
             poly([(cx, cy + gh - h), (cx + g, cy - h), (cx + g, cy), (cx, cy + gh)], fill=right)]
        top_pts = [(cx, cy - gh - h), (cx + g, cy - h), (cx, cy + gh - h), (cx - g, cy - h)]
        if level >= 4:
            pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in top_pts)
            t.append(f'<polygon points="{pts}" fill="{topc}" filter="url(#glow)"><animate attributeName="fill" '
                     f'values="{topc};#ffc070;{topc}" dur="{3 + random.random() * 2:.1f}s" repeatCount="indefinite"/></polygon>')
        else:
            t.append(poly(top_pts, fill=topc))
        t.append('</g>')
        towers.append(''.join(t))
    a('<g>' + ''.join(floor) + '</g>')
    # a slow band of firelight travelling down the road
    n = len(weeks)
    road = ' '.join(f'{x:.0f},{y:.0f}' for x, y in [(ox, oy - hh), (ox + n * hw, oy + (n - 1) * hh),
                                                     (ox + (n - 7) * hw, oy + (n + 6) * hh), (ox - 7 * hw, oy + 6 * hh)])
    a(f'<clipPath id="road"><polygon points="{road}"/></clipPath>')
    a('<g clip-path="url(#road)" style="mix-blend-mode:screen"><rect x="-300" y="150" width="260" height="420" fill="url(#sweep)" transform="skewX(-63)">'
      '<animate attributeName="x" values="200;1700" dur="9s" repeatCount="indefinite"/></rect></g>')
    a('<g>' + ''.join(towers) + '</g>')

    # month names along the near edge
    seen = None
    for wi, week in enumerate(weeks):
        first = datetime.date.fromisoformat(week[0][0])
        if first.month != seen and wi < len(weeks) - 1:
            seen = first.month
            x = ox + (wi - 7) * hw - 4
            y = oy + (wi + 7) * hh + 16
            a(text(f'{x:.0f}', f'{y:.0f}', first.strftime('%b').upper(), 10, '#5e4a3a', spacing=2))

    # fog and embers
    a('<g filter="url(#soft)" fill="#6d1b20" opacity="0.22"><ellipse cx="350" cy="600" rx="430" ry="44">'
      '<animate attributeName="cx" values="350;520;350" dur="28s" repeatCount="indefinite"/></ellipse>'
      '<ellipse cx="950" cy="610" rx="420" ry="40"><animate attributeName="cx" values="950;780;950" dur="34s" repeatCount="indefinite"/></ellipse></g>')
    a('<g fill="#ff7a2e" filter="url(#glow)">')
    for _ in range(16):
        x, r, dur, begin, end = random.randint(30, 1170), random.choice([1.2, 1.5, 2]), random.randint(8, 16), \
            random.random() * 12, random.randint(60, 320)
        drift = random.randint(-40, 40)
        a(f'<circle cx="{x}" cy="640" r="{r}" opacity="0"><animate attributeName="cy" values="640;{end}" dur="{dur}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="cx" values="{x};{x + drift}" dur="{dur}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;0.95;0" dur="{dur}s" begin="{begin:.1f}s" repeatCount="indefinite"/></circle>')
    a('</g>')

    # ---- heading
    a(text(64, 70, 'THE RECORD OF DEEDS', 30, BONE, spacing=9, extra=' filter="url(#glow)"'))
    a('<rect x="64" y="86" width="430" height="1.2" fill="url(#rule)"/>')
    a(text(66, 110, f'{days[0][0]}  —  {days[-1][0]}', 14, DIM, spacing=3))

    # ---- numbers (upper right)
    stats = [(str(total), 'DEEDS THIS YEAR'), (str(current), 'NIGHTS UNBROKEN'),
             (str(longest), 'LONGEST VIGIL'), (str(top), 'FIERCEST NIGHT')]
    for i, (num, label) in enumerate(stats):
        x = 690 + (i % 2) * 245
        y = 392 + (i // 2) * 106
        big = i == 0
        a(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{1.2 + i * 0.35:.2f}s" dur="1.2s" fill="freeze"/>'
          + text(x, y, num, 62 if big else 50, '#f1c36a' if big else BONE, extra=' filter="url(#glow)"')
          + text(x + 2, y + 26, label, 13, GOLD, spacing=4) + '</g>')

    # ---- tongues (lower left)
    a(text(64, 470, 'TONGUES SPOKEN', 14, GOLD, spacing=5))
    size = sum(langs.values()) or 1
    for i, (name, n) in enumerate(sorted(langs.items(), key=lambda e: -e[1])[:4]):
        y = 494 + i * 26
        pct = 100 * n / size
        width = max(3, 190 * n / size)
        a(text(64, y + 5, name, 16, BONE))
        a(f'<rect x="170" y="{y - 5}" width="190" height="7" fill="#1a0a0d"/>')
        a(f'<rect x="170" y="{y - 5}" width="0" height="7" fill="url(#bar)"><animate attributeName="width" from="0" to="{width:.0f}" '
          f'begin="{1.6 + i * 0.25:.2f}s" dur="1.4s" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1" fill="freeze"/></rect>')
        a(text(372, y + 5, f'{pct:.0f}%', 14, DIM))

    a(f'<rect width="{W}" height="{H}" filter="url(#grain)"/>')
    a(f'</g><rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" stroke="#3a1215"/></svg>')
    return '\n'.join(o)


def main():
    if '--demo' in sys.argv or '--demo-sparse' in sys.argv:
        weeks, langs = demo('--demo-sparse' in sys.argv)
    else:
        weeks, langs = fetch(os.environ['USERNAME'], os.environ['GITHUB_TOKEN'])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(build(weeks, langs))
    print('wrote', os.path.normpath(OUT))


if __name__ == '__main__':
    main()
