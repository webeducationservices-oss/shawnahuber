#!/usr/bin/env python3
"""
Update sitemap.xml and blog.html listing to include all 58 blog posts.
"""
import os, re, json, glob, html as html_lib
from datetime import datetime

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(SITE_DIR, 'blog')
POSTS_JSON = os.path.join(SITE_DIR, 'blog-posts', 'all-posts.json')

with open(POSTS_JSON, 'r') as f:
    all_posts = json.load(f)

print(f"Total blog posts in metadata: {len(all_posts)}")

# Sort by publish_date descending (newest first)
def sort_key(p):
    try:
        return datetime.fromisoformat(p.get('publish_date', '2000-01-01'))
    except Exception:
        return datetime.fromisoformat('2000-01-01')

all_posts.sort(key=sort_key, reverse=True)

# ── Update sitemap.xml ──
print("\n1. Updating sitemap.xml...")
sitemap_path = os.path.join(SITE_DIR, 'sitemap.xml')

today = datetime.now().strftime('%Y-%m-%d')

# Build the URL list
root_urls = [
    ('https://shawnahuber.com/', '1.0'),
    ('https://shawnahuber.com/about', '0.8'),
    ('https://shawnahuber.com/programs', '0.8'),
    ('https://shawnahuber.com/business-owner', '0.7'),
    ('https://shawnahuber.com/equestrian', '0.7'),
    ('https://shawnahuber.com/baseball', '0.7'),
    ('https://shawnahuber.com/soccer', '0.7'),
    ('https://shawnahuber.com/speaking', '0.7'),
    ('https://shawnahuber.com/mastermind', '0.7'),
    ('https://shawnahuber.com/products', '0.6'),
    ('https://shawnahuber.com/blog', '0.8'),
    ('https://shawnahuber.com/contact', '0.7'),
]

blog_urls = [(f'https://shawnahuber.com/blog/{p["path"]}', '0.5') for p in all_posts]

sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url, priority in root_urls + blog_urls:
    sitemap_xml += f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>{priority}</priority>\n  </url>\n'
sitemap_xml += '</urlset>\n'

with open(sitemap_path, 'w') as f:
    f.write(sitemap_xml)
print(f"  ✓ Sitemap updated with {len(root_urls + blog_urls)} URLs")

# ── Update blog.html listing ──
print("\n2. Updating blog.html listing...")
blog_html_path = os.path.join(SITE_DIR, 'blog.html')
with open(blog_html_path, 'r') as f:
    blog_html = f.read()

def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%B %d, %Y').replace(' 0', ' ')
    except Exception:
        return iso_str

def esc(text):
    return html_lib.escape(text or '', quote=True)

# Build new blog grid HTML
cards_html = ''
for p in all_posts:
    title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', p.get('title', '').strip())
    desc = p.get('description', '')
    if not desc:
        desc = ''
    # Truncate desc
    if len(desc) > 140:
        desc = desc[:137] + '...'

    # Get thumbnail - prefer local image
    slug = p['path']
    # Check if there's a local image with the slug as name
    thumb = ''
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        local = os.path.join(SITE_DIR, 'images', 'blog', f'{slug}{ext}')
        if os.path.exists(local):
            thumb = f'images/blog/{slug}{ext}'
            break
    # Fallback to thumbnail URL from metadata if it's local
    if not thumb:
        thumb_url = ''
        if p.get('thumbnail') and p['thumbnail'].get('url'):
            thumb_url = p['thumbnail']['url']
        elif p.get('main_image') and p['main_image'].get('url'):
            thumb_url = p['main_image']['url']
        # If it's a local path, use it
        if thumb_url.startswith('/images/') or thumb_url.startswith('images/'):
            thumb = thumb_url.lstrip('/')
        else:
            # External URL - use a default
            thumb = 'images/Shawn Black Shirt-1920w.jpeg'

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

# Find and replace the blog grid section
new_grid = f'      <div class="blog-grid">\n{cards_html}      </div>'

# Match the existing grid
pattern = r'<div class="blog-grid">.*?</div>\s*\n\s*</div>\s*\n\s*</section>'
match = re.search(pattern, blog_html, re.DOTALL)
if match:
    # Replace just the grid contents
    blog_html = re.sub(
        r'<div class="blog-grid">.*?</div>(\s*\n\s*</div>\s*\n\s*</section>)',
        new_grid + r'\1',
        blog_html, count=1, flags=re.DOTALL
    )
else:
    # Try simpler pattern
    blog_html = re.sub(
        r'<div class="blog-grid">.*?</div>',
        new_grid,
        blog_html, count=1, flags=re.DOTALL
    )

with open(blog_html_path, 'w') as f:
    f.write(blog_html)
print(f"  ✓ Blog listing updated with {len(all_posts)} cards")

# ── Update related-posts sidebars in blog posts ──
# For now, the existing sidebar uses metadata from all-posts.json, which is updated.
# But the related posts in the posts already point to the existing 3 most recent.
# To refresh, we'd need to regenerate sidebars. Skip for now since this is fine.

print("\n✓ Done!")
