#!/usr/bin/env python3
"""
Apply a new global navigation to every HTML page.
Adds a utility bar (phone + social icons), reorganizes the main nav into
4 main items (Programs, About, Resources, Contact) with rich dropdowns
and a prominent Schedule a Call CTA button.
"""
import os, re, glob

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_nav(prefix):
    """Build the nav HTML with the right relative prefix (./ or ../)"""
    return f'''<!-- Top utility bar -->
  <div class="nav-utility">
    <div class="nav-utility-inner">
      <div class="nav-utility-left">
        <a href="tel:9198243530"><i class="fas fa-phone"></i> (919) 824-3530</a>
        <a href="mailto:structuredfreedom@gmail.com" class="nav-utility-email"><i class="fas fa-envelope"></i> structuredfreedom@gmail.com</a>
      </div>
      <div class="nav-utility-right">
        <a href="https://www.facebook.com/groups/227824444972533" target="_blank" rel="noopener noreferrer" aria-label="Facebook"><i class="fab fa-facebook-f"></i></a>
        <a href="https://www.instagram.com/shawnhuber3" target="_blank" rel="noopener noreferrer" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
        <a href="https://www.linkedin.com/in/thementalmechanic" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn"><i class="fab fa-linkedin-in"></i></a>
        <a href="https://www.youtube.com/@thementalmechanic" target="_blank" rel="noopener noreferrer" aria-label="YouTube"><i class="fab fa-youtube"></i></a>
      </div>
    </div>
  </div>

  <nav class="nav">
    <div class="nav-inner">
      <a href="{prefix}index.html" class="nav-logo" aria-label="The Mental Mechanics — Home">
        <img src="{prefix}images/Mental Mechanics Logo with tagline Green-1920w.png" alt="The Mental Mechanics" width="200" height="50">
      </a>
      <div class="nav-links">
        <div class="dropdown">
          <a href="{prefix}programs.html" class="dropdown-trigger">Programs <i class="fas fa-chevron-down"></i></a>
          <div class="dropdown-menu">
            <div class="dropdown-section">Get Started</div>
            <a href="{prefix}programs.html"><i class="fas fa-compass"></i><span><strong>How It Works</strong><br><small style="color:var(--gray-500);font-weight:400">Our coaching approach</small></span></a>
            <div class="dropdown-divider"></div>
            <div class="dropdown-section">Mindset Mastery Courses</div>
            <a href="{prefix}business-owner.html"><i class="fas fa-briefcase"></i>For Business Owners</a>
            <a href="{prefix}equestrian.html"><i class="fas fa-horse"></i>For Equestrians</a>
            <a href="{prefix}baseball.html"><i class="fas fa-baseball"></i>For Baseball Players</a>
            <a href="{prefix}soccer.html"><i class="fas fa-futbol"></i>For Soccer Players</a>
            <a href="{prefix}teen-girls-sports.html"><i class="fas fa-star"></i>For Teen Girls in Sports</a>
            <div class="dropdown-divider"></div>
            <a href="{prefix}mastermind.html"><i class="fas fa-users"></i>Mastermind Group</a>
            <a href="{prefix}speaking.html"><i class="fas fa-microphone"></i>Speaking & Events</a>
          </div>
        </div>
        <a href="{prefix}about.html">About</a>
        <div class="dropdown">
          <a href="{prefix}blog.html" class="dropdown-trigger">Resources <i class="fas fa-chevron-down"></i></a>
          <div class="dropdown-menu">
            <a href="{prefix}blog.html"><i class="fas fa-pen-fancy"></i>Blog</a>
            <a href="{prefix}assessment.html"><i class="fas fa-clipboard-check"></i>Free Assessment</a>
            <a href="{prefix}products.html"><i class="fas fa-shopping-bag"></i>Recommended Products</a>
            <a href="{prefix}index.html#challenge"><i class="fas fa-bolt"></i>5-Day Mindset Challenge</a>
          </div>
        </div>
        <a href="{prefix}contact.html">Contact</a>
        <a href="{prefix}contact.html" class="btn btn-primary btn-sm nav-cta"><i class="fas fa-calendar-check" style="margin-right:6px"></i>Schedule a Call</a>
      </div>
      <div class="mobile-toggle" aria-label="Toggle menu" role="button" tabindex="0">
        <span></span><span></span><span></span>
      </div>
    </div>
  </nav>'''

def replace_nav(html, new_nav):
    """Replace existing <nav class="nav">...</nav> (and any preceding nav-utility)"""
    # Remove any existing nav-utility (in case we re-run)
    html = re.sub(
        r'<!-- Top utility bar -->\s*<div class="nav-utility">.*?</div>\s*</div>\s*</div>\s*',
        '',
        html, flags=re.DOTALL
    )
    # Replace the <nav class="nav"> block
    pattern = re.compile(r'<nav class="nav">.*?</nav>', re.DOTALL)
    return pattern.sub(new_nav, html, count=1)

# Process all HTML files
root_files = glob.glob(os.path.join(SITE_DIR, '*.html'))
blog_files = glob.glob(os.path.join(SITE_DIR, 'blog', '*.html'))

print(f"Updating navigation in {len(root_files)} root + {len(blog_files)} blog files...\n")

for f in sorted(root_files):
    filename = os.path.basename(f)
    # Determine if this page is "active" in any nav item
    page_active = ''
    if filename == 'index.html':
        page_active = 'home'
    elif filename in ('programs.html', 'business-owner.html', 'equestrian.html', 'baseball.html', 'soccer.html', 'teen-girls-sports.html', 'mastermind.html', 'speaking.html'):
        page_active = 'programs'
    elif filename in ('blog.html', 'assessment.html', 'products.html'):
        page_active = 'resources'
    elif filename == 'about.html':
        page_active = 'about'
    elif filename == 'contact.html':
        page_active = 'contact'

    nav_html = build_nav('')

    # Inject .active class on the right top-level item
    if page_active == 'about':
        nav_html = nav_html.replace('<a href="about.html">About</a>', '<a href="about.html" class="active">About</a>')
    elif page_active == 'contact':
        nav_html = nav_html.replace('<a href="contact.html">Contact</a>', '<a href="contact.html" class="active">Contact</a>')
    elif page_active == 'programs':
        nav_html = nav_html.replace('class="dropdown-trigger">Programs', 'class="dropdown-trigger active">Programs')
    elif page_active == 'resources':
        nav_html = nav_html.replace('class="dropdown-trigger">Resources', 'class="dropdown-trigger active">Resources')

    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    new_content = replace_nav(content, nav_html)
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(new_content)
        print(f"  ✓ {filename}")

# Blog post files (use ../ prefix, mark Resources active)
nav_html_blog = build_nav('../')
nav_html_blog = nav_html_blog.replace('class="dropdown-trigger">Resources', 'class="dropdown-trigger active">Resources')

for f in sorted(blog_files):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    new_content = replace_nav(content, nav_html_blog)
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(new_content)

print(f"  ✓ Updated {len(blog_files)} blog posts")
print("\n✓ Done!")
