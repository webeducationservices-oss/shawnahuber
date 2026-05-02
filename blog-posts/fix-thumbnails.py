#!/usr/bin/env python3
"""
Fix blog.html thumbnails by extracting the actual hero image
from each post's HTML file.
"""
import os, re, json, glob, html as html_lib, urllib.parse
from datetime import datetime

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(SITE_DIR, 'blog')
POSTS_JSON = os.path.join(SITE_DIR, 'blog-posts', 'all-posts.json')

with open(POSTS_JSON, 'r') as f:
    all_posts = json.load(f)

# Sort by date desc
def sort_key(p):
    try:
        return datetime.fromisoformat(p.get('publish_date', '2000-01-01'))
    except Exception:
        return datetime.fromisoformat('2000-01-01')

all_posts.sort(key=sort_key, reverse=True)

def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%B %d, %Y').replace(' 0', ' ')
    except Exception:
        return iso_str

def esc(text):
    return html_lib.escape(text or '', quote=True)

def extract_hero_image(blog_html_path):
    """Extract the actual hero image src from a blog post HTML"""
    if not os.path.exists(blog_html_path):
        return None
    with open(blog_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Look for blog-article-hero class
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class="blog-article-hero"', content)
    if m:
        return m.group(1)
    m = re.search(r'class="blog-article-hero"[^>]*src=["\']([^"\']+)["\']', content)
    if m:
        return m.group(1)
    return None

# Build cards
print("Extracting hero images from each blog post...")
cards_html = ''
for p in all_posts:
    slug = p['path']
    title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', p.get('title', '').strip())
    desc = p.get('description', '')
    if not desc:
        desc = ''
    if len(desc) > 140:
        desc = desc[:137] + '...'

    # Get the actual hero image used in the post
    blog_path = os.path.join(BLOG_DIR, f'{slug}.html')
    hero_src = extract_hero_image(blog_path)

    if hero_src:
        # Convert ../images/blog/foo.jpg to images/blog/foo.jpg (relative to site root)
        if hero_src.startswith('../'):
            thumb = hero_src[3:]
        elif hero_src.startswith('/'):
            thumb = hero_src.lstrip('/')
        else:
            thumb = hero_src
    else:
        # Fallback
        thumb = 'images/Shawn Black Shirt-1920w.jpeg'
        print(f"  ! No hero found for {slug}, using fallback")

    date_display = format_date(p.get('publish_date', ''))
    author = p.get('author_name', 'Shawn Huber')

    cards_html += f'''        <a href="blog/{slug}.html" class="blog-card">
          <img src="{thumb}" alt="{esc(title)}" class="blog-card-img" loading="lazy" width="400" height="240">
          <div class="blog-card-body">
            <h3>{esc(title)}</h3>
            <div class="blog-card-meta">{esc(author)} &middot; {date_display}</div>
            <p>{esc(desc)}</p>
            <span class="read-more">Read article &rarr;</span>
          </div>
        </a>
'''

# Update blog.html
blog_html_path = os.path.join(SITE_DIR, 'blog.html')
with open(blog_html_path, 'r') as f:
    blog_html = f.read()

new_grid = f'      <div class="blog-grid">\n{cards_html}      </div>'

blog_html = re.sub(
    r'<div class="blog-grid">.*?</div>(\s*\n\s*</div>\s*\n\s*</section>)',
    new_grid + r'\1',
    blog_html, count=1, flags=re.DOTALL
)

with open(blog_html_path, 'w') as f:
    f.write(blog_html)

print(f"\n✓ Updated blog.html with {len(all_posts)} cards using actual hero images")

# ── Also fix sidebar related-posts in each blog post ──
print("\nUpdating related-posts sidebars in all blog posts...")

# Build a map of slug → (title, hero_path, date)
post_meta = {}
for p in all_posts:
    slug = p['path']
    blog_path = os.path.join(BLOG_DIR, f'{slug}.html')
    hero = extract_hero_image(blog_path)
    if hero and hero.startswith('../'):
        # Already has correct ../ prefix for blog/ context
        sidebar_thumb = hero
    elif hero and hero.startswith('/'):
        sidebar_thumb = '..' + hero
    elif hero:
        sidebar_thumb = '../' + hero
    else:
        sidebar_thumb = '../images/Shawn Black Shirt-1920w.jpeg'

    title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', p.get('title', '').strip())
    date_display = format_date(p.get('publish_date', ''))
    post_meta[slug] = {
        'title': title,
        'thumb': sidebar_thumb,
        'date': date_display,
    }

# Now update each blog post's sidebar
sidebar_pattern = re.compile(
    r'(<div class="sidebar-card">\s*<div class="sidebar-head">\s*<h4>Recent Posts</h4>\s*</div>\s*<div class="sidebar-body">)(.*?)(</div>\s*</div>)',
    re.DOTALL
)

updated_sidebars = 0
for current_slug in post_meta:
    blog_path = os.path.join(BLOG_DIR, f'{current_slug}.html')
    if not os.path.exists(blog_path):
        continue

    with open(blog_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pick 3 related (other slugs)
    related_slugs = [s for s in post_meta if s != current_slug][:3]
    related_html = ''
    for rs in related_slugs:
        meta = post_meta[rs]
        related_html += f'''            <a href="{rs}.html" class="sidebar-link">
              <img src="{meta['thumb']}" alt="{esc(meta['title'])}" class="sidebar-link-img" width="60" height="60" loading="lazy">
              <div>
                <h5>{esc(meta['title'])}</h5>
                <span>{meta['date']}</span>
              </div>
            </a>
'''

    new_content, count = sidebar_pattern.subn(
        r'\1\n' + related_html + '          \3',
        content, count=1
    )

    if count > 0:
        with open(blog_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated_sidebars += 1

print(f"✓ Updated sidebars in {updated_sidebars} blog posts")
