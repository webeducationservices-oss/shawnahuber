#!/usr/bin/env python3
"""
Migrate missing blog posts from the RSS feed.
Extracts title, content, pubDate, image for each missing slug,
then generates HTML files using the same template.
"""
import os, re, html as html_lib, urllib.request, urllib.parse, json
from datetime import datetime
from xml.etree import ElementTree as ET

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(SITE_DIR, 'blog')
IMG_DIR = os.path.join(SITE_DIR, 'images', 'blog')
RSS_FILE = '/tmp/shawnahuber-rss.xml'

# Read existing all-posts.json to find next IDs etc.
POSTS_JSON = os.path.join(SITE_DIR, 'blog-posts', 'all-posts.json')
with open(POSTS_JSON, 'r') as f:
    existing_posts = json.load(f)

existing_slugs = {p['path'] for p in existing_posts}

# Parse RSS
ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
tree = ET.parse(RSS_FILE)
root = tree.getroot()
channel = root.find('channel')

CONTENT_NS = '{http://purl.org/rss/1.0/modules/content/}'

def safe_filename(url):
    parsed = urllib.parse.urlparse(url)
    base = os.path.basename(parsed.path)
    base = urllib.parse.unquote(base).replace('+', ' ')
    if '.' not in base:
        base += '.jpg'
    base = re.sub(r'[^\w.\-+() ]', '_', base)
    return base[:120] if len(base) > 120 else base

def download_image(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) < 100:
                return False
            with open(dest, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"    ! Image fail: {url} → {e}")
        return False

def parse_pub_date(pub_str):
    """Parse RFC 822 date to ISO"""
    try:
        # e.g. "Thu, 01 May 2026 13:33:00 +0000" or similar
        for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S GMT', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.strptime(pub_str, fmt)
                return dt.strftime('%Y-%m-%dT%H:%M:%S')
            except ValueError:
                continue
    except Exception:
        pass
    return '2024-01-01T12:00:00'

def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%B %d, %Y').replace(' 0', ' ')
    except Exception:
        return iso_str

def extract_first_image(html_content):
    """Find first image URL in content"""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_content)
    return m.group(1) if m else None

def clean_content(html_content):
    """Clean RSS content for embedding"""
    # Decode HTML entities
    content = html_lib.unescape(html_content)
    # Remove carriage returns
    content = content.replace('\r', '')
    # Remove data-rss-type wrappers
    content = re.sub(r'<div data-rss-type="[^"]*">\s*', '', content)
    # Clean up extra whitespace inside tags
    content = re.sub(r'>\s+<', '><', content)
    # Remove inline images that we'll handle separately (the main image is in content)
    # Strip leading/trailing whitespace
    return content.strip()

def esc(text):
    return html_lib.escape(text, quote=True)

def json_esc(text):
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def get_related_posts(current_slug, all_posts, count=3):
    """Pick 3 related posts (just first N excluding current)"""
    others = [p for p in all_posts if p['path'] != current_slug]
    return others[:count]

def build_html(slug, title, description, body_content, hero_img_local, pub_iso, all_posts_meta):
    clean_title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', title).strip()
    date_display = format_date(pub_iso)
    date_iso = pub_iso[:10]

    # Description fallback
    if not description:
        text = re.sub(r'<[^>]+>', '', body_content)
        text = re.sub(r'\s+', ' ', text).strip()
        description = text[:155] + '...' if len(text) > 155 else text

    # Build related posts sidebar
    related = get_related_posts(slug, all_posts_meta)
    related_html = ''
    for rp in related:
        rp_title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', rp.get('title', '')).strip()
        rp_thumb = ''
        if rp.get('thumbnail') and rp['thumbnail'].get('url'):
            rp_thumb = rp['thumbnail']['url']
        elif rp.get('main_image') and rp['main_image'].get('url'):
            rp_thumb = rp['main_image']['url']
        rp_date = format_date(rp.get('publish_date', ''))
        related_html += f'''            <a href="{rp['path']}.html" class="sidebar-link">
              <img src="{rp_thumb}" alt="{esc(rp_title)}" class="sidebar-link-img" width="60" height="60" loading="lazy">
              <div>
                <h5>{esc(rp_title)}</h5>
                <span>{rp_date}</span>
              </div>
            </a>
'''

    hero_html = f'<img src="../images/blog/{urllib.parse.quote(hero_img_local)}" alt="{esc(clean_title)}" class="blog-article-hero" width="800" height="420">' if hero_img_local else ''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(clean_title)} | The Mental Mechanics</title>
  <meta name="description" content="{esc(description)}">
  <link rel="icon" type="image/svg+xml" href="../images/favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="stylesheet" href="../styles.css">
  <link rel="canonical" href="https://shawnahuber.com/blog/{slug}">
  <meta property="og:title" content="{esc(clean_title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="https://shawnahuber.com/images/blog/{urllib.parse.quote(hero_img_local) if hero_img_local else ''}">
  <meta property="og:url" content="https://shawnahuber.com/blog/{slug}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="The Mental Mechanics">
  <meta property="article:published_time" content="{pub_iso}">
  <meta property="article:author" content="Shawn Huber">
  <script src="../script.js" defer></script>
  <!-- Google Consent Mode v2 -->
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('consent', 'default', {{
      'analytics_storage': 'granted',
      'ad_storage': 'denied',
      'ad_user_data': 'denied',
      'ad_personalization': 'denied'
    }});
  </script>
  <!-- Google Tag Manager -->
  <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
  new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
  }})(window,document,'script','dataLayer','GTM-5LVJJFV');</script>
  <!-- End Google Tag Manager -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{json_esc(clean_title)}",
    "description": "{json_esc(description)}",
    "image": "https://shawnahuber.com/images/blog/{urllib.parse.quote(hero_img_local) if hero_img_local else ''}",
    "datePublished": "{date_iso}",
    "author": {{
      "@type": "Person",
      "name": "Shawn Huber",
      "url": "https://shawnahuber.com/about",
      "jobTitle": "High-Performance Mindset Coach",
      "worksFor": {{
        "@type": "Organization",
        "name": "The Mental Mechanics"
      }}
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "The Mental Mechanics",
      "url": "https://shawnahuber.com",
      "logo": {{
        "@type": "ImageObject",
        "url": "https://shawnahuber.com/images/Mental Mechanics Logo with tagline Green-1920w.png"
      }}
    }},
    "mainEntityOfPage": {{
      "@type": "WebPage",
      "@id": "https://shawnahuber.com/blog/{slug}"
    }}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://shawnahuber.com/" }},
      {{ "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://shawnahuber.com/blog" }},
      {{ "@type": "ListItem", "position": 3, "name": "{json_esc(clean_title)}", "item": "https://shawnahuber.com/blog/{slug}" }}
    ]
  }}
  </script>
</head>
<body>
  <!-- Google Tag Manager (noscript) -->
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-5LVJJFV"
  height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
  <!-- End Google Tag Manager (noscript) -->

  <nav class="nav">
    <div class="nav-inner">
      <a href="../index.html" class="nav-logo">
        <img src="../images/Mental Mechanics Logo with tagline Green-1920w.png" alt="The Mental Mechanics" width="200" height="50">
      </a>
      <div class="nav-links">
        <div class="dropdown">
          <a href="../programs.html" class="dropdown-trigger">Programs <i class="fas fa-chevron-down" style="font-size:0.6rem;margin-left:4px"></i></a>
          <div class="dropdown-menu">
            <a href="../programs.html">How It Works</a>
            <a href="../business-owner.html">Business Owner Mindset Mastery</a>
            <a href="../equestrian.html">Equestrian Mindset Mastery</a>
            <a href="../baseball.html">Baseball Mindset Mastery</a>
            <a href="../soccer.html">Soccer Mindset Mastery</a>
            <a href="../speaking.html">Speaking</a>
          </div>
        </div>
        <a href="../about.html">About</a>
        <a href="../products.html">Products</a>
        <a href="../blog.html" class="active">Blog</a>
        <a href="../contact.html">Contact</a>
        <a href="../contact.html" class="btn btn-primary btn-sm nav-cta">Schedule a Call</a>
      </div>
      <div class="mobile-toggle">
        <span></span><span></span><span></span>
      </div>
    </div>
  </nav>

  <main>

  <section class="section" style="padding-top:100px">
    <div class="blog-back-row">
      <a href="../blog.html" class="blog-back-link"><i class="fas fa-arrow-left"></i> Back to Blog</a>
    </div>
    <div class="blog-post-layout">
      <article class="blog-article">
        {hero_html}
        <div class="blog-article-header">
          <h1>{clean_title}</h1>
          <div class="blog-article-meta">
            <i class="fas fa-user"></i> Shawn Huber
            <span>&middot;</span>
            <i class="fas fa-calendar"></i> <time datetime="{date_iso}">{date_display}</time>
          </div>
        </div>
        <div class="blog-article-body">
          {body_content}
        </div>

        <div class="blog-author-box">
          <img src="../images/Shawn Black Shirt-1920w.jpeg" alt="Shawn Huber" class="blog-author-avatar" width="72" height="72">
          <div>
            <h4>Shawn Huber</h4>
            <div class="author-title">High-Performance Mindset Coach</div>
            <p>Shawn Huber is the founder of The Mental Mechanics, specializing in mindset coaching for business owners, athletes, and high performers. With expertise in hypnosis, NLP, and performance psychology, Shawn helps clients break through mental barriers and achieve lasting success.</p>
          </div>
        </div>
      </article>

      <aside class="blog-sidebar">
        <div class="sidebar-card">
          <div class="sidebar-head">
            <h4>About the Author</h4>
          </div>
          <div class="sidebar-body">
            <p>Shawn Huber is the founder of The Mental Mechanics, a high-performance mindset coaching practice based in Palm Harbor, FL.</p>
            <p><a href="../about.html" style="color:var(--green);font-weight:500">Learn more about Shawn &rarr;</a></p>
          </div>
        </div>

        <div class="sidebar-card">
          <div class="sidebar-head">
            <h4>Recent Posts</h4>
          </div>
          <div class="sidebar-body">
{related_html}          </div>
        </div>

        <div class="sidebar-cta">
          <h4>Ready to Transform Your Mindset?</h4>
          <p>Schedule a free consultation and discover how mindset coaching can help you reach your full potential.</p>
          <a href="../contact.html" class="btn btn-gold">Schedule a Call</a>
        </div>

        <div class="sidebar-card">
          <div class="sidebar-head">
            <h4>Programs</h4>
          </div>
          <div class="sidebar-body">
            <a href="../business-owner.html" class="sidebar-link">
              <div>
                <h5>Business Owner Mindset Mastery</h5>
                <span>12-session course</span>
              </div>
            </a>
            <a href="../equestrian.html" class="sidebar-link">
              <div>
                <h5>Equestrian Mindset Mastery</h5>
                <span>Performance coaching</span>
              </div>
            </a>
            <a href="../baseball.html" class="sidebar-link">
              <div>
                <h5>Baseball Mindset Mastery</h5>
                <span>Mental training system</span>
              </div>
            </a>
            <a href="../soccer.html" class="sidebar-link">
              <div>
                <h5>Soccer Mindset Mastery</h5>
                <span>Mental training system</span>
              </div>
            </a>
          </div>
        </div>
      </aside>
    </div>
  </section>

  </main>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <img src="../images/Mental Mechanics Logo Horizontal-1920w.png" alt="The Mental Mechanics" width="180" height="45">
          <p>High-performance mindset coaching for entrepreneurs, athletes, and leaders. Live happier and healthier.</p>
          <div class="footer-social">
            <a href="https://www.facebook.com/groups/227824444972533" target="_blank" rel="noopener noreferrer" aria-label="Facebook"><i class="fab fa-facebook-f"></i></a>
            <a href="https://www.instagram.com/shawnhuber3" target="_blank" rel="noopener noreferrer" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
            <a href="https://www.linkedin.com/in/thementalmechanic" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn"><i class="fab fa-linkedin-in"></i></a>
            <a href="https://www.tiktok.com/@thementalmechanic" target="_blank" rel="noopener noreferrer" aria-label="TikTok"><i class="fab fa-tiktok"></i></a>
            <a href="https://www.youtube.com/@thementalmechanic" target="_blank" rel="noopener noreferrer" aria-label="YouTube"><i class="fab fa-youtube"></i></a>
          </div>
        </div>
        <div>
          <h5>Pages</h5>
          <div class="footer-links">
            <a href="../index.html">Home</a>
            <a href="../about.html">About</a>
            <a href="../programs.html">Programs</a>
            <a href="../speaking.html">Speaking</a>
            <a href="../blog.html">Blog</a>
          </div>
        </div>
        <div>
          <h5>Programs</h5>
          <div class="footer-links">
            <a href="../business-owner.html">Business Owner Course</a>
            <a href="../equestrian.html">Equestrian Course</a>
            <a href="../baseball.html">Baseball System</a>
            <a href="../soccer.html">Soccer System</a>
            <a href="../products.html">Recommended Products</a>
          </div>
        </div>
        <div>
          <h5>Contact</h5>
          <div class="footer-links">
            <a href="tel:9198243530"><i class="fas fa-phone" style="margin-right:6px"></i> (919) 824-3530</a>
            <a href="mailto:structuredfreedom@gmail.com"><i class="fas fa-envelope" style="margin-right:6px"></i> Email Us</a>
            <a href="../contact.html"><i class="fas fa-calendar" style="margin-right:6px"></i> Schedule a Call</a>
          </div>
          <p style="font-size:0.85rem;margin-top:1rem;color:var(--gray-500)">Palm Harbor, FL 34685<br>Mon - Fri, 9am - 5pm ET</p>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2025 The Mental Mechanics. All Rights Reserved.</span>
        <span>Mind, Body, and Business</span>
        <span style="font-size:11px;color:#999;">Protected by reCAPTCHA. <a href="https://policies.google.com/privacy" style="color:#999;">Privacy</a> &middot; <a href="https://policies.google.com/terms" style="color:#999;">Terms</a></span>
      </div>
    </div>
  </footer>

  <button class="scroll-top" aria-label="Scroll to top"><i class="fas fa-chevron-up"></i></button>
</body>
</html>
'''

# Process each missing item from RSS
new_meta = []
processed = 0
for item in channel.findall('item'):
    title_elem = item.find('title')
    link_elem = item.find('link')
    desc_elem = item.find('description')
    content_elem = item.find(f'{CONTENT_NS}encoded')
    pub_elem = item.find('pubDate')

    if title_elem is None or link_elem is None:
        continue

    title = title_elem.text or ''
    link = link_elem.text or ''
    slug = link.rstrip('/').split('/')[-1]

    if slug in existing_slugs:
        continue

    description = desc_elem.text if desc_elem is not None else ''
    content_html = content_elem.text if content_elem is not None else ''
    pub_date = pub_elem.text if pub_elem is not None else ''

    print(f"\nMigrating: {slug}")
    print(f"  Title: {title}")

    pub_iso = parse_pub_date(pub_date)

    # Find first image in content
    img_url = extract_first_image(content_html or '')
    hero_local = None
    if img_url:
        # Decode HTML entities in URL
        img_url = html_lib.unescape(img_url)
        hero_local = safe_filename(img_url)
        dest = os.path.join(IMG_DIR, hero_local)
        if download_image(img_url, dest):
            print(f"  ✓ Image: {hero_local}")
        else:
            print(f"  ✗ Image failed")
            hero_local = None

    # Clean content - strip the first image from content (used as hero)
    cleaned_body = clean_content(content_html or '')
    if img_url and img_url in cleaned_body:
        # Remove the first occurrence of the hero image
        cleaned_body = re.sub(r'<img[^>]+src=["\'][^"\']*' + re.escape(os.path.basename(img_url)) + r'[^"\']*["\'][^>]*>', '', cleaned_body, count=1)

    # Generate HTML
    html_output = build_html(slug, title, description, cleaned_body, hero_local, pub_iso, existing_posts)
    output_path = os.path.join(BLOG_DIR, f'{slug}.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Track for metadata update
    new_meta.append({
        'id': slug.replace('-', '')[:32],
        'path': slug,
        'status': 'PUBLISHED',
        'creation_date': pub_iso,
        'publish_date': pub_iso,
        'title': title,
        'author_name': 'Shawn Huber',
        'meta_title': None,
        'description': description,
        'tags': [],
        'no_index': None,
        'thumbnail': {
            'url': f'/images/blog/{hero_local}' if hero_local else '',
            'alt_text': None
        },
        'main_image': {
            'url': f'/images/blog/{hero_local}' if hero_local else ''
        }
    })

    processed += 1
    print(f"  ✓ Created: blog/{slug}.html")

# Update all-posts.json with new entries
existing_posts.extend(new_meta)
with open(POSTS_JSON, 'w') as f:
    json.dump(existing_posts, f, indent=2)

print(f"\n{'='*60}")
print(f"Migrated {processed} blog posts. Total now: {len(existing_posts)}")
