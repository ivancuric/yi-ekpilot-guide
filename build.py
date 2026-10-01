#!/usr/bin/env python3
"""Regenerate sw.js from index.html.

VERSION    = first 10 hex chars of sha1(index.html); it names the shell cache, so any page
             change makes returning visitors pick up the new page.
CARD_FILES = sorted card image paths the page references; the service worker precaches
             exactly these and evicts any other card it has cached.

    python3 build.py           rewrite sw.js in place
    python3 build.py --check   exit 1 if sw.js is stale or a card file is missing (no writes)
"""
import hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
PAGE, SW, CARDS = ROOT / 'index.html', ROOT / 'sw.js', ROOT / 'cards'

def build():
    page = PAGE.read_bytes()
    version = hashlib.sha1(page).hexdigest()[:10]
    cards = sorted(set(re.findall(r'cards/[0-9a-f]+\.avif', page.decode('utf-8'))))
    sw = SW.read_text(encoding='utf-8')
    sw, n1 = re.subn(r"^const VERSION='[0-9a-f]*';$", f"const VERSION='{version}';", sw, flags=re.M)
    sw, n2 = re.subn(r'^const CARD_FILES=\[.*?\];$', lambda _: f'const CARD_FILES={json.dumps(cards)};', sw, flags=re.M)
    if (n1, n2) != (1, 1):
        sys.exit('build.py: sw.js no longer has exactly one VERSION and one CARD_FILES line')
    return version, cards, sw

def main():
    check = '--check' in sys.argv[1:]
    version, cards, sw = build()
    errors = []
    missing = [c for c in cards if not (ROOT / c).is_file()]
    if missing:
        errors.append(f'{len(missing)} card file(s) referenced but missing: ' + ', '.join(missing))
    orphans = sorted(f'cards/{p.name}' for p in CARDS.glob('*.avif') if f'cards/{p.name}' not in cards)
    if orphans:  # harmless (never precached), but dead weight in the deploy
        print(f'build.py: {len(orphans)} unreferenced card file(s): ' + ', '.join(orphans), file=sys.stderr)
    stale = SW.read_text(encoding='utf-8') != sw
    if check:
        if stale:
            errors.append(f'sw.js is stale (page is {version}); run python3 build.py')
    elif stale:
        SW.write_text(sw, encoding='utf-8', newline='\n')
        print(f'sw.js updated: VERSION {version}, {len(cards)} cards')
    else:
        print(f'sw.js up to date: VERSION {version}, {len(cards)} cards')
    if errors:
        sys.exit('build.py: ' + '\nbuild.py: '.join(errors))

if __name__ == '__main__':
    main()
