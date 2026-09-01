#!/usr/bin/env python3
"""One-off: load real photographs from shawnahuber.com into the WES Studio
photo library for studio.shawnahuber.com. Idempotent via studio_photos.external_id."""
import os, re, json, glob, uuid, hashlib, mimetypes, urllib.request, urllib.parse
from PIL import Image

SITE_DIR = '/Users/justinbabcock/Desktop/Websites/ShawnAHuber/site'
SITE_ID  = '8b7d8ade-bfb3-4450-a0e4-43b013aa06a3'
BUCKET   = 'studio-photos'

env = {}
for line in open('/Users/justinbabcock/Desktop/Websites/.env.keys'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.split('=', 1); env[k.strip()] = v.strip()
SB, KEY = env['SUPABASE_PROJECT_URL'], env['SUPABASE_SERVICE_ROLE_KEY']
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}

def api(method, path, body=None, extra=None, raw=None, ctype='application/json'):
    hdr = dict(H); hdr.update(extra or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: hdr['Content-Type'] = ctype
    r = urllib.request.Request(SB + path, data=data, headers=hdr, method=method)
    with urllib.request.urlopen(r, timeout=90) as resp:
        b = resp.read()
        return json.loads(b) if b and b[:1] in b'[{' else b

CHROME = ('favicon','apple-touch','logo','icon','mental-mechanic')  # wordmark banners too
# Normalise Duda size variants so "-640w" and "-1920w" collapse to one asset
def stem(p):
    n = os.path.splitext(os.path.basename(p))[0]
    return re.sub(r'-(?:\d{3,4})w$', '', n).strip().lower()

def album_for(path, w, h):
    if '/blog/' in path:                 return 'Website — Blog & Article Imagery'
    n = os.path.basename(path).lower()
    if n.startswith('pexels') or any(k in n for k in ('energyplus','gbx-','happy-juice')):
        return 'Website — Stock & Product'
    return 'Website — Photos of Shawn'

# ---- collect, filter, dedupe (keep the largest of each variant group) ----
best = {}
for f in sorted(glob.glob(f'{SITE_DIR}/images/*') + glob.glob(f'{SITE_DIR}/images/blog/*')):
    if not os.path.isfile(f): continue
    ext = os.path.splitext(f)[1].lower()
    if ext not in ('.jpg','.jpeg','.png','.webp'): continue
    n = os.path.basename(f).lower()
    if any(k in n for k in CHROME): continue
    try:
        with Image.open(f) as im: w, h = im.size
    except Exception: continue
    if w < 500 or h < 400: continue                     # too small to post
    k = stem(f)
    if k not in best or w*h > best[k][1]*best[k][2]:
        best[k] = (f, w, h)

# drop byte-identical duplicates that survived naming differences
seen, picks = set(), []
for f, w, h in sorted(best.values()):
    d = hashlib.md5(open(f,'rb').read()).hexdigest()
    if d in seen: continue
    seen.add(d); picks.append((f, w, h))

print(f"importing {len(picks)} photos (from {len(best)} deduped names)\n")

# ---- albums ----
album_names = sorted({album_for(f,w,h) for f,w,h in picks})
albums = {}
for i, name in enumerate(album_names):
    # on_conflict must name the unique constraint or PostgREST 409s on re-run
    api('POST', '/rest/v1/studio_albums?on_conflict=site_id,name',
        {'site_id': SITE_ID, 'name': name, 'position': i, 'sync_source': 'website',
         'description': 'Imported from shawnahuber.com'},
        {'Prefer': 'resolution=ignore-duplicates,return=minimal'})
    got = api('GET', f'/rest/v1/studio_albums?site_id=eq.{SITE_ID}&name=eq.{urllib.parse.quote(name)}&select=id')
    albums[name] = got[0]['id']
    print(f"  album: {name}")
print()

def ig_ok(w,h):
    r = w/h
    return 0.80 <= r <= 1.91

ok = skip = fail = 0
warn = []
for f, w, h in picks:
    rel = os.path.relpath(f, SITE_DIR)                  # external_id = stable identity
    exists = api('GET', f"/rest/v1/studio_photos?site_id=eq.{SITE_ID}"
                        f"&external_id=eq.{urllib.parse.quote(rel)}&select=id")
    if exists:
        skip += 1; continue
    ext  = os.path.splitext(f)[1].lower()
    path = f"{SITE_ID}/{uuid.uuid4()}{ext}"
    ctype = mimetypes.guess_type(f)[0] or 'image/jpeg'
    try:
        api('POST', f'/storage/v1/object/{BUCKET}/{path}',
            raw=open(f,'rb').read(), ctype=ctype,
            extra={'x-upsert':'true','cache-control':'31536000'})
    except Exception as e:
        print(f"  ! upload failed {os.path.basename(f)}: {str(e)[:70]}"); fail += 1; continue
    url = f"{SB}/storage/v1/object/public/{BUCKET}/{path}"
    label = re.sub(r'[-_]+',' ', stem(f)).strip().title()
    api('POST', '/rest/v1/studio_photos',
        {'site_id': SITE_ID, 'storage_path': path, 'url': url, 'label': label,
         'width': w, 'height': h, 'album_id': albums[album_for(f,w,h)],
         'source': 'website', 'external_id': rel, 'media_type': 'image',
         'uploaded_by': 'justin@webeducationservices.com'},
        {'Prefer':'return=minimal'})
    ok += 1
    if not ig_ok(w,h): warn.append((os.path.basename(f), f"{w}x{h}", round(w/h,2)))

print(f"\nuploaded {ok} | already present {skip} | failed {fail}")
if warn:
    print(f"\n{len(warn)} outside Instagram's 0.80–1.91 ratio (the picker will flag them):")
    for n,d,r in warn: print(f"    {d:>11}  ratio {r:<5} {n[:52]}")
