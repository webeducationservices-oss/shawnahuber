#!/usr/bin/env python3
"""
Update all blog post HTML files with:
- 2-column layout (article + sidebar)
- Article JSON-LD schema
- Author bio box
- Sidebar with related posts + CTA
- Remove old inline styles
"""
import json, os, re, html
from datetime import datetime

SITE_DIR = os.path.join(os.path.dirname(__file__), '..')
BLOG_DIR = os.path.join(SITE_DIR, 'blog')
POSTS_JSON = os.path.join(os.path.dirname(__file__), 'all-posts.json')

with open(POSTS_JSON, 'r') as f:
    all_posts = json.load(f)

# Build lookup by path
posts_by_path = {p['path']: p for p in all_posts}

def format_date(date_str):
    """Convert 2022-06-29T16:43:23 to June 29, 2022"""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%B %d, %Y').replace(' 0', ' ')
    except:
        return date_str

def get_related_posts(current_path, count=3):
    """Get related posts (just pick nearby posts from the list, excluding current)"""
    others = [p for p in all_posts if p['path'] != current_path and p.get('title')]
    # Return first N that aren't the current post
    return others[:count]

def extract_body_content(html_content):
    """Extract the blog article body content from existing HTML"""
    # Try to find blog-article-body div content
    match = re.search(r'<div class="blog-article-body">(.*?)</div>\s*</div>', html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try blog-post-article body pattern
    match = re.search(r'<div class="blog-article-body">(.*?)</div>', html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ''

def extract_hero_image(html_content):
    """Extract hero image URL from existing HTML"""
    # Look for blog-post-hero-img pattern
    match = re.search(r'<div class="blog-post-hero-img">\s*<img src="([^"]+)"', html_content)
    if match:
        return match.group(1)
    # Look for blog-article-hero
    match = re.search(r'class="blog-article-hero"[^>]*src="([^"]+)"', html_content)
    if match:
        return match.group(1)
    return ''

def extract_title(html_content):
    """Extract h1 title from existing HTML"""
    match = re.search(r'<h1>(.*?)</h1>', html_content)
    if match:
        return match.group(1).strip()
    return ''

def extract_og_image(html_content):
    """Extract og:image from meta tags"""
    match = re.search(r'<meta property="og:image" content="([^"]+)"', html_content)
    if match:
        return match.group(1)
    return ''

def esc(text):
    """Escape for HTML attributes and JSON"""
    return html.escape(text, quote=True)

def json_esc(text):
    """Escape for JSON strings"""
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def build_blog_html(path, post_data, body_content, hero_img):
    title = post_data.get('title', '').strip()
    # Clean title - remove " | Mental Mechanics" suffix
    clean_title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', title)

    author = post_data.get('author_name', 'Shawn Huber')
    if author.upper() == 'THE MENTAL MECHANICS':
        author = 'Shawn Huber'

    publish_date = post_data.get('publish_date', '')
    date_display = format_date(publish_date)
    date_iso = publish_date[:10] if publish_date else ''

    description = post_data.get('description', '')
    if not description:
        # Generate from body content
        text = re.sub(r'<[^>]+>', '', body_content)
        text = re.sub(r'\s+', ' ', text).strip()
        description = text[:155] + '...' if len(text) > 155 else text

    thumbnail = ''
    if post_data.get('thumbnail') and post_data['thumbnail'].get('url'):
        thumbnail = post_data['thumbnail']['url']
    if not thumbnail and post_data.get('main_image') and post_data['main_image'].get('url'):
        thumbnail = post_data['main_image']['url']
    if not thumbnail:
        thumbnail = hero_img

    if not hero_img:
        hero_img = thumbnail

    related = get_related_posts(path)

    # Build related posts sidebar HTML
    related_html = ''
    for rp in related:
        rp_title = rp.get('title', '').strip()
        rp_title = re.sub(r'\s*\|\s*Mental Mechanics\s*$', '', rp_title)
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

    # Hero image HTML
    hero_html = ''
    if hero_img:
        hero_html = f'        <img src="{hero_img}" alt="{esc(clean_title)}" class="blog-article-hero" width="800" height="420">'

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
  <link rel="canonical" href="https://shawnahuber.com/blog/{path}">
  <meta property="og:title" content="{esc(clean_title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="{thumbnail}">
  <meta property="og:url" content="https://shawnahuber.com/blog/{path}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="The Mental Mechanics">
  <meta property="article:published_time" content="{publish_date}">
  <meta property="article:author" content="{esc(author)}">
  <script src="../script.js" defer></script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{json_esc(clean_title)}",
    "description": "{json_esc(description)}",
    "image": "{thumbnail}",
    "datePublished": "{date_iso}",
    "author": {{
      "@type": "Person",
      "name": "{json_esc(author)}",
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
      "@id": "https://shawnahuber.com/blog/{path}"
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
      {{ "@type": "ListItem", "position": 3, "name": "{json_esc(clean_title)}", "item": "https://shawnahuber.com/blog/{path}" }}
    ]
  }}
  </script>
</head>
<body>

  <nav class="nav">
    <div class="nav-inner">
      <a href="../index.html" class="nav-logo">
        <img src="../images/Mental Mechanics Logo with tagline Green-1920w.png" alt="The Mental Mechanics">
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
            <i class="fas fa-user"></i> {esc(author)}
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
          <img src="../images/Mental Mechanics Logo Horizontal-1920w.png" alt="The Mental Mechanics">
          <p>High-performance mindset coaching for entrepreneurs, athletes, and leaders. Live happier and healthier.</p>
          <div class="footer-social">
            <a href="https://www.facebook.com/groups/227824444972533" target="_blank" aria-label="Facebook"><i class="fab fa-facebook-f"></i></a>
            <a href="https://www.instagram.com/shawnhuber3" target="_blank" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
            <a href="https://www.linkedin.com/in/thementalmechanic" target="_blank" aria-label="LinkedIn"><i class="fab fa-linkedin-in"></i></a>
            <a href="https://www.tiktok.com/@thementalmechanic" target="_blank" aria-label="TikTok"><i class="fab fa-tiktok"></i></a>
            <a href="https://www.youtube.com/@thementalmechanic" target="_blank" aria-label="YouTube"><i class="fab fa-youtube"></i></a>
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

def process_blog_file(filepath):
    """Process a single blog HTML file"""
    filename = os.path.basename(filepath)
    path = filename.replace('.html', '')

    # Read existing content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract body content
    body = extract_body_content(content)
    if not body:
        print(f"  SKIP (no body content): {filename}")
        return False

    # Extract hero image
    hero_img = extract_hero_image(content)
    if not hero_img:
        hero_img = extract_og_image(content)

    # Get post data from JSON
    post_data = posts_by_path.get(path)
    if not post_data:
        # Try to build minimal post data from HTML
        title = extract_title(content)
        if not title:
            print(f"  SKIP (no post data or title): {filename}")
            return False
        post_data = {
            'path': path,
            'title': title,
            'author_name': 'Shawn Huber',
            'publish_date': '',
            'description': '',
            'thumbnail': {'url': hero_img},
            'main_image': {'url': hero_img}
        }
        # Try to extract date from existing HTML
        date_match = re.search(r'<i class="fas fa-calendar"></i>\s*(.+?)(?:\s*<|\s*$)', content)
        if date_match:
            post_data['publish_date'] = date_match.group(1).strip()

    # Build new HTML
    new_html = build_blog_html(path, post_data, body, hero_img)

    # Write updated file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"  OK: {filename}")
    return True

# Process all blog files
print("Updating blog post templates...")
count = 0
skip = 0
for filename in sorted(os.listdir(BLOG_DIR)):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(BLOG_DIR, filename)
    if process_blog_file(filepath):
        count += 1
    else:
        skip += 1

print(f"\nDone! Updated: {count}, Skipped: {skip}")
