#!/usr/bin/env python3
"""
Global rebrand propagation across all HTML pages:
- Footer tagline
- Nav dropdown labels (Programs -> Coaching; Mindset Mastery Courses -> Who I Help; subtitle)
- Footer "Programs" column heading + link text
- Blog author bios (inline box + sidebar card)
"""
import os, glob

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (old, new) exact string replacements applied everywhere
REPLACEMENTS = [
    # Footer brand tagline
    (
        "High-performance mindset coaching for entrepreneurs, athletes, and leaders. Live happier and healthier.",
        "Mental wellness coaching for high achievers. Private and group sessions for entrepreneurs, athletes, and leaders who want their inner game to match their outer drive.",
    ),
    # Nav dropdown trigger label
    (
        '<a href="programs.html" class="dropdown-trigger">Programs <i class="fas fa-chevron-down"></i></a>',
        '<a href="programs.html" class="dropdown-trigger">Coaching <i class="fas fa-chevron-down"></i></a>',
    ),
    (
        '<a href="../programs.html" class="dropdown-trigger">Programs <i class="fas fa-chevron-down"></i></a>',
        '<a href="../programs.html" class="dropdown-trigger">Coaching <i class="fas fa-chevron-down"></i></a>',
    ),
    # Nav dropdown trigger label with active class (current page = programs/audience pages)
    (
        '<a href="programs.html" class="dropdown-trigger active">Programs <i class="fas fa-chevron-down"></i></a>',
        '<a href="programs.html" class="dropdown-trigger active">Coaching <i class="fas fa-chevron-down"></i></a>',
    ),
    (
        '<a href="../programs.html" class="dropdown-trigger active">Programs <i class="fas fa-chevron-down"></i></a>',
        '<a href="../programs.html" class="dropdown-trigger active">Coaching <i class="fas fa-chevron-down"></i></a>',
    ),
    # Nav dropdown "Get Started" section: How It Works subtitle
    (
        '<a href="programs.html"><i class="fas fa-compass"></i><span><strong>How It Works</strong><br><small style="color:var(--gray-500);font-weight:400">Our coaching approach</small></span></a>',
        '<a href="programs.html"><i class="fas fa-compass"></i><span><strong>How It Works</strong><br><small style="color:var(--gray-500);font-weight:400">Private &amp; group sessions</small></span></a>',
    ),
    (
        '<a href="../programs.html"><i class="fas fa-compass"></i><span><strong>How It Works</strong><br><small style="color:var(--gray-500);font-weight:400">Our coaching approach</small></span></a>',
        '<a href="../programs.html"><i class="fas fa-compass"></i><span><strong>How It Works</strong><br><small style="color:var(--gray-500);font-weight:400">Private &amp; group sessions</small></span></a>',
    ),
    # Nav dropdown section label
    (
        '<div class="dropdown-section">Mindset Mastery Courses</div>',
        '<div class="dropdown-section">Who I Help</div>',
    ),
    # Footer "Programs" column heading
    (
        '<h5>Programs</h5>',
        '<h5>Coaching</h5>',
    ),
    # Footer Programs column link text (root pages)
    ('<a href="business-owner.html">Business Owner Course</a>', '<a href="business-owner.html">For Entrepreneurs</a>'),
    ('<a href="equestrian.html">Equestrian Course</a>', '<a href="equestrian.html">For Equestrians</a>'),
    ('<a href="baseball.html">Baseball System</a>', '<a href="baseball.html">For Baseball Players</a>'),
    ('<a href="soccer.html">Soccer System</a>', '<a href="soccer.html">For Soccer Players</a>'),
    # Footer Programs column link text (blog pages with ../)
    ('<a href="../business-owner.html">Business Owner Course</a>', '<a href="../business-owner.html">For Entrepreneurs</a>'),
    ('<a href="../equestrian.html">Equestrian Course</a>', '<a href="../equestrian.html">For Equestrians</a>'),
    ('<a href="../baseball.html">Baseball System</a>', '<a href="../baseball.html">For Baseball Players</a>'),
    ('<a href="../soccer.html">Soccer System</a>', '<a href="../soccer.html">For Soccer Players</a>'),
    # Blog author box bio (inline, under article)
    (
        "Shawn Huber is the founder of The Mental Mechanics, specializing in mindset coaching for business owners, athletes, and high performers. With expertise in hypnosis, NLP, and performance psychology, Shawn helps clients break through mental barriers and achieve lasting success.",
        "Shawn Huber is the founder of The Mental Mechanics, a mental wellness coach for high achievers. Through private and group sessions, he helps entrepreneurs, athletes, and leaders think clearer, perform stronger, and recover faster &mdash; with expertise in performance coaching, hypnotherapy, and 25+ years of experience.",
    ),
    # Blog sidebar author card
    (
        "Shawn Huber is the founder of The Mental Mechanics, a high-performance mindset coaching practice based in Palm Harbor, FL.",
        "Shawn Huber is the founder of The Mental Mechanics, a mental wellness coaching practice for high achievers based in Palm Harbor, FL.",
    ),
]

files = glob.glob(os.path.join(SITE_DIR, '*.html')) + glob.glob(os.path.join(SITE_DIR, 'blog', '*.html'))

total_changes = 0
files_changed = 0
per_replacement = {old[:45]: 0 for old, _ in REPLACEMENTS}

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content
    for old, new in REPLACEMENTS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            per_replacement[old[:45]] += count
            total_changes += count
    if content != original:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)
        files_changed += 1

print(f"Files changed: {files_changed} / {len(files)}")
print(f"Total replacements: {total_changes}\n")
print("Per-replacement counts:")
for k, v in per_replacement.items():
    print(f"  [{v:3}] {k}...")
