#!/usr/bin/env python3
"""
Fix remaining SEO issues:
1. Add rel="noopener noreferrer" to target="_blank" links missing it
2. Shorten blog titles that exceed 65 chars (preserve original H1)
3. Fix blog descriptions: pad short ones, truncate long ones
4. Add width/height to img tags missing them
"""
import os, re, glob, json

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(SITE_DIR, 'blog')

# ── Fix 1: Add rel="noopener noreferrer" to all target="_blank" links ──
print("Fix 1: Adding rel=noopener noreferrer to unsafe links...")
fixed_links = 0
files = glob.glob(os.path.join(SITE_DIR, '*.html')) + glob.glob(os.path.join(BLOG_DIR, '*.html'))

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content

    # Match <a ...target="_blank"... > that don't already have noopener
    def add_rel(m):
        global fixed_links
        tag = m.group(0)
        if 'rel=' in tag:
            # Has rel already, ensure noopener + noreferrer
            def upgrade_rel(rm):
                rel = rm.group(1)
                parts = set(rel.split())
                parts.add('noopener')
                parts.add('noreferrer')
                return f'rel="{" ".join(sorted(parts))}"'
            new_tag = re.sub(r'rel=["\']([^"\']*)["\']', upgrade_rel, tag)
        else:
            # Inject rel before >
            new_tag = tag[:-1].rstrip() + ' rel="noopener noreferrer">'
        if new_tag != tag:
            fixed_links += 1
        return new_tag

    content = re.sub(r'<a\s+[^>]*target="_blank"[^>]*>', add_rel, content)

    if content != original:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)

print(f"  Fixed {fixed_links} links")

# ── Fix 2: Add missing width/height to <img> tags ──
print("\nFix 2: Adding width/height to img tags...")
img_fixed = 0

def add_dimensions(match):
    global img_fixed
    tag = match.group(0)
    attrs = match.group(1) if match.groups() else ''

    has_width = 'width=' in tag
    has_height = 'height=' in tag

    if has_width and has_height:
        return tag

    # Skip if no src (or is a tracking pixel)
    if 'src=' not in tag:
        return tag

    # Determine dimensions based on context
    width = '600'
    height = '400'

    # Sidebar thumbnails
    if 'sidebar-link-img' in tag:
        width = '60'; height = '60'
    elif 'blog-author-avatar' in tag:
        width = '72'; height = '72'
    elif 'blog-card-img' in tag:
        width = '400'; height = '240'
    elif 'blog-article-hero' in tag or 'hero-img' in tag:
        width = '800'; height = '420'
    elif 'program-icon' in tag:
        width = '64'; height = '64'
    elif 'footer' in tag.lower() and 'logo' in tag.lower():
        width = '180'; height = '45'
    elif 'nav-logo' in tag or 'logo' in tag.lower():
        width = '200'; height = '50'

    # Add width and height if missing
    if not has_width:
        tag = tag[:-1] + f' width="{width}">'
    if not has_height:
        tag = tag[:-1] + f' height="{height}">'

    img_fixed += 1
    return tag

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content
    content = re.sub(r'<img\s+[^>]*>', add_dimensions, content)
    if content != original:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)

print(f"  Added dimensions to {img_fixed} img tags")

# ── Fix 3: Shorten blog titles that exceed 65 chars ──
print("\nFix 3: Shortening long blog post titles...")

def fix_title_length(text, max_len=60):
    """Truncate title smartly while preserving meaning"""
    if len(text) <= max_len:
        return text
    # Try truncating at a word boundary
    truncated = text[:max_len].rsplit(' ', 1)[0]
    return truncated.rstrip(',.;:-')

title_fixed = 0
for f in glob.glob(os.path.join(BLOG_DIR, '*.html')):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content

    # Find current title
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if not title_match:
        continue
    current_title = title_match.group(1)

    # Parse out post title vs " | The Mental Mechanics" suffix
    suffix = ' | The Mental Mechanics'
    if current_title.endswith(suffix):
        post_title = current_title[:-len(suffix)]
    else:
        post_title = current_title

    if len(current_title) > 65:
        # Budget: 65 total - 23 for suffix = 42 chars for post title
        new_post_title = fix_title_length(post_title, 42)
        new_title = new_post_title + suffix

        # Replace <title>
        content = content.replace(f'<title>{current_title}</title>', f'<title>{new_title}</title>', 1)

        # Also replace og:title
        content = re.sub(
            r'(<meta\s+property=["\']og:title["\']\s+content=["\'])([^"\']+)(["\'])',
            lambda m: m.group(1) + new_post_title + m.group(3),
            content, count=1
        )

        if content != original:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(content)
            title_fixed += 1

print(f"  Shortened {title_fixed} titles")

# ── Fix 4: Fix blog descriptions ──
print("\nFix 4: Fixing blog post descriptions...")
desc_fixed = 0

for f in glob.glob(os.path.join(BLOG_DIR, '*.html')):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content

    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', content)
    if not desc_match:
        continue
    desc = desc_match.group(1)

    new_desc = None
    if len(desc) > 170:
        # Truncate smart
        new_desc = desc[:155].rsplit(' ', 1)[0].rstrip(',.;:-') + '...'
    elif len(desc) < 120:
        # Pad with CTA
        if '.' not in desc[-5:]:
            desc = desc + '.'
        cta = ' Read more insights from The Mental Mechanics.'
        needed = 140 - len(desc)
        if needed > len(cta):
            new_desc = desc + cta + ' Schedule a free consultation today.'
        else:
            new_desc = desc + cta
        # Ensure it's between 120-170
        if len(new_desc) > 170:
            new_desc = new_desc[:167] + '...'

    if new_desc and new_desc != desc:
        # Escape quotes for HTML
        def replace_desc(match):
            attr = match.group(1)
            return f'<meta {attr} content="{new_desc}"'
        content = re.sub(
            r'<meta\s+(name=["\']description["\']|property=["\']og:description["\'])\s+content=["\'][^"\']*["\']',
            replace_desc, content
        )
        if content != original:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(content)
            desc_fixed += 1

print(f"  Fixed {desc_fixed} descriptions")

print("\n✓ SEO fixes complete!")
