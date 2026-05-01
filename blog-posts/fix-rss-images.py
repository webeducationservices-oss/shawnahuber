#!/usr/bin/env python3
"""
Fix image collisions for RSS-migrated posts.
Each post should have its own image file, named after the slug.
Also try to find images for posts that didn't get one.
"""
import os, re, urllib.request, urllib.parse, html as html_lib
from xml.etree import ElementTree as ET

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(SITE_DIR, 'blog')
IMG_DIR = os.path.join(SITE_DIR, 'images', 'blog')
RSS_FILE = '/tmp/shawnahuber-rss.xml'
CONTENT_NS = '{http://purl.org/rss/1.0/modules/content/}'

# 15 RSS-migrated slugs
RSS_SLUGS = {
    'visualization-techniques-for-improved-performance',
    'how-healthy-is-your-business',
    'better-business-results-through-hypnosis',
    'how-hypnosis-works-according-to-science',
    'why-do-i-think-the-coaching-and-most-services-based-business-will-implode-soon',
    'does-money-really-affect-motivation',
    'an-unhealthy-successful-business',
    'get-your-vibe-back-with-this-mental-mechanic-tool-the-box-breath',
    'how-to-have-both-productive-and-recovery-time-for-huge-success',
    'does-health-make-wealth-or-wealth-make-health',
    'self-evaluation-vs-self-reflection',
    '5-causes-of-mental-burnout-in-business-professionals',
    'how-to-deal-with-business-owner-burnout',
    'why-is-running-a-business-so-stressful',
    'can-stress-and-anxiety-affect-your-body',
}

# Parse RSS
tree = ET.parse(RSS_FILE)
channel = tree.getroot().find('channel')

# Build slug → all images map
post_images = {}
for item in channel.findall('item'):
    link = item.find('link').text or ''
    slug = link.rstrip('/').split('/')[-1]
    if slug not in RSS_SLUGS:
        continue
    content_elem = item.find(f'{CONTENT_NS}encoded')
    content = content_elem.text if content_elem is not None else ''
    if not content:
        continue
    content = html_lib.unescape(content)
    # Find all images
    images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    # Also check media:content / enclosure
    post_images[slug] = images

def download_image(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) < 500:
                return False
            with open(dest, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"    ✗ Download fail: {e}")
        return False

# Process each post
print(f"Processing {len(RSS_SLUGS)} RSS-migrated posts...\n")
for slug in sorted(RSS_SLUGS):
    images = post_images.get(slug, [])
    print(f"\n{slug}")
    print(f"  Found {len(images)} image(s) in content")

    if not images:
        print(f"  ⊘ No images found")
        continue

    # Use the first image as hero
    hero_url = images[0]
    parsed = urllib.parse.urlparse(hero_url)
    ext = os.path.splitext(parsed.path)[1] or '.jpg'
    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        ext = '.jpg'

    # Use slug as filename
    new_filename = f'{slug}{ext}'
    dest = os.path.join(IMG_DIR, new_filename)

    if download_image(hero_url, dest):
        print(f"  ✓ Downloaded as {new_filename} ({os.path.getsize(dest)} bytes)")
    else:
        print(f"  ✗ Failed to download {hero_url}")
        continue

    # Update HTML file
    html_path = os.path.join(BLOG_DIR, f'{slug}.html')
    if not os.path.exists(html_path):
        print(f"  ⚠ No HTML file at {html_path}")
        continue

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    original = html_content

    # Replace the old "blog_post_image.png" reference with the new unique filename
    html_content = html_content.replace(
        '../images/blog/blog_post_image.png',
        f'../images/blog/{urllib.parse.quote(new_filename)}'
    )
    html_content = html_content.replace(
        '/images/blog/blog_post_image.png',
        f'/images/blog/{urllib.parse.quote(new_filename)}'
    )

    # Also handle case where post had NO image originally — inject hero
    if '<img' not in html_content[:2500] and 'blog-article-hero' not in html_content:
        # Need to add hero image to article header
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
        title = title_match.group(1) if title_match else slug
        hero_img = f'<img src="../images/blog/{urllib.parse.quote(new_filename)}" alt="{title}" class="blog-article-hero" width="800" height="420">'
        html_content = re.sub(
            r'(<article class="blog-article">\s*)\n',
            r'\1\n        ' + hero_img + '\n',
            html_content, count=1
        )

    if html_content != original:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  ✓ Updated HTML to use new image")

# Delete the colliding shared image
shared = os.path.join(IMG_DIR, 'blog_post_image.png')
if os.path.exists(shared):
    os.remove(shared)
    print(f"\n✓ Removed shared blog_post_image.png")

print("\nDone!")
