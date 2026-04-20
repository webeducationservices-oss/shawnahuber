#!/usr/bin/env python3
"""
Download all Duda CDN images locally and rewrite HTML to use local paths.
Removes the external dependency on Duda's infrastructure.
"""
import os, re, glob, hashlib, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

SITE_DIR = os.path.join(os.path.dirname(__file__), '..')
IMG_DIR = os.path.join(SITE_DIR, 'images', 'blog')
os.makedirs(IMG_DIR, exist_ok=True)

# Patterns to match Duda CDN URLs
DUDA_PATTERN = re.compile(r'https://irp\.cdn-website\.com/[^\s"\'>)]+')
GDRIVE_PATTERN = re.compile(r'https://lh3\.googleusercontent\.com/d/[^\s"\'>)]+')

def safe_filename(url):
    """Generate a safe local filename from a URL"""
    # Get the path after the domain
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    # Extract just the filename part
    base = os.path.basename(path)
    # URL-decode it (e.g., +20copy → ' copy')
    base = urllib.parse.unquote(base).replace('+', ' ')
    # If it has no extension, try to guess from URL structure or default to jpg
    if '.' not in base:
        # Use hash to avoid collisions
        h = hashlib.md5(url.encode()).hexdigest()[:8]
        base = f"image-{h}.jpg"
    # Clean up filename - replace special chars
    base = re.sub(r'[^\w.\-+() ]', '_', base)
    # Truncate if too long
    if len(base) > 120:
        name, ext = os.path.splitext(base)
        base = name[:115] + ext
    return base

def download_image(url, dest_path):
    """Download an image with browser-like headers"""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True  # Already downloaded
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) < 100:
                print(f"  ! Too small ({len(data)}b): {url}")
                return False
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  ! Failed: {url} — {e}")
        return False

# Step 1: Collect all unique Duda + GDrive URLs
print("Step 1: Scanning HTML files for external image URLs...")
all_urls = set()
html_files = glob.glob(os.path.join(SITE_DIR, '*.html')) + glob.glob(os.path.join(SITE_DIR, 'blog', '*.html'))

for f in html_files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    for url in DUDA_PATTERN.findall(content):
        all_urls.add(url)
    for url in GDRIVE_PATTERN.findall(content):
        all_urls.add(url)

print(f"  Found {len(all_urls)} unique external image URLs")

# Step 2: Build URL → local path mapping
print("\nStep 2: Building URL mapping...")
url_to_local = {}
used_names = {}
for url in sorted(all_urls):
    fname = safe_filename(url)
    # Handle collisions
    base, ext = os.path.splitext(fname)
    counter = 1
    while fname in used_names.values():
        fname = f"{base}-{counter}{ext}"
        counter += 1
    used_names[url] = fname
    url_to_local[url] = fname

# Step 3: Download all images in parallel
print(f"\nStep 3: Downloading {len(url_to_local)} images to {IMG_DIR}...")
success = 0
failed = 0
failed_urls = []

def download_task(url, fname):
    dest = os.path.join(IMG_DIR, fname)
    ok = download_image(url, dest)
    return url, fname, ok

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(download_task, url, fname) for url, fname in url_to_local.items()]
    for i, future in enumerate(as_completed(futures), 1):
        url, fname, ok = future.result()
        if ok:
            success += 1
        else:
            failed += 1
            failed_urls.append(url)
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(url_to_local)}")

print(f"\n  Downloaded: {success}, Failed: {failed}")
if failed_urls:
    print(f"  Failed URLs:")
    for url in failed_urls[:10]:
        print(f"    {url}")

# Step 4: Rewrite HTML files
print("\nStep 4: Rewriting HTML files...")
# For URLs that failed to download, we'll leave them alone (don't break images)
rewrite_map = {url: fname for url, fname in url_to_local.items() if url not in failed_urls}

replaced_count = 0
files_updated = 0
for f in html_files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()

    original = content
    # Determine correct relative path based on file location
    is_blog_subdir = '/blog/' in f or f.endswith('/blog/') or os.path.dirname(f).endswith('blog')
    prefix = '../images/blog/' if is_blog_subdir else 'images/blog/'

    for url, fname in rewrite_map.items():
        if url in content:
            content = content.replace(url, prefix + urllib.parse.quote(fname))
            replaced_count += content.count(prefix + urllib.parse.quote(fname))

    if content != original:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)
        files_updated += 1

print(f"  Updated {files_updated} HTML files")

# Step 5: Verify no Duda URLs remain
print("\nStep 5: Verifying...")
remaining = 0
for f in html_files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    remaining += len(DUDA_PATTERN.findall(content)) + len(GDRIVE_PATTERN.findall(content))
print(f"  Remaining external image URLs in HTML: {remaining}")
if remaining > 0:
    print(f"  (These likely failed to download - left intact to avoid broken images)")

print("\nDone!")
