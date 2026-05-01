#!/usr/bin/env python3
"""
Use Claude API to restructure each blog post body content with:
- Proper H2/H3 headers (SEO + scannability)
- Callout boxes for key insights
- FAQ sections where Q&As fit
- Two-column comparisons where relevant
- Step cards for numbered processes
- Pull quotes for impactful statements
- CTA card at end
- Key takeaways box

Preserves all original content meaning. Only restructures.
"""
import os, re, sys, json, glob, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(SITE_DIR, 'blog')

# Read API key from env.keys
ENV_KEYS = '/Users/justinbabcock/Desktop/Websites/.env.keys'
ANTHROPIC_API_KEY = None
with open(ENV_KEYS) as f:
    for line in f:
        if line.startswith('ANTHROPIC_API_KEY='):
            ANTHROPIC_API_KEY = line.split('=', 1)[1].strip()
            break

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found")
    sys.exit(1)

MODEL = 'claude-sonnet-4-20250514'

ENHANCEMENT_PROMPT = """You are an expert UX writer and SEO content editor for a high-performance mindset coaching website (The Mental Mechanics by Shawn Huber).

I'm giving you the body content of a blog post. The current HTML is messy: H2 tags contain entire paragraphs, lists are embedded in paragraphs as "1.", "2.", "3.", and there are unclosed tags.

Your job: Restructure this content into clean, scannable, SEO-optimized HTML.

# REQUIREMENTS

**1. Structure with semantic HTML**
- Open with a 1-2 paragraph compelling intro (no header above it)
- Add 3-6 H2 section headers throughout (descriptive, keyword-rich, around 4-8 words each)
- Use H3 subheaders within sections when appropriate
- Convert numbered "1. ... 2. ... 3." text into proper `<ol>` lists OR step cards (see below)
- Convert bullet-like lists into `<ul>`
- Break long walls of text into shorter paragraphs (2-4 sentences max)

**2. Use these custom components where they FIT NATURALLY (don't force them):**

Callout box (for key insights, tips, or warnings):
```html
<div class="callout callout-tip">
  <div class="callout-icon"><i class="fas fa-lightbulb"></i></div>
  <div class="callout-body">
    <h4>Coach's Insight</h4>
    <p>Quote or insight here.</p>
  </div>
</div>
```
Variants: `callout-tip` (lightbulb), `callout-info` (info-circle), `callout-warning` (exclamation-triangle), `callout-key` (key)

Pull quote (for impactful statements):
```html
<blockquote class="blog-pullquote">
  Powerful sentence pulled from the content.
  <cite>— Key Insight</cite>
</blockquote>
```

Step cards (for numbered processes — use INSTEAD of `<ol>` when each step has a paragraph of explanation):
```html
<div class="blog-step">
  <div class="blog-step-num">1</div>
  <div class="blog-step-body">
    <h4>Step Title</h4>
    <p>Explanation paragraph.</p>
  </div>
</div>
```

Two-column section (for comparisons, before/after, do/don't):
```html
<div class="blog-two-col">
  <div>
    <h3>Left Column Title</h3>
    <p>Content...</p>
  </div>
  <div>
    <h3>Right Column Title</h3>
    <p>Content...</p>
  </div>
</div>
```

Key takeaways box (1-2 per post, summarizing main points):
```html
<div class="blog-takeaways">
  <h3><i class="fas fa-star"></i> Key Takeaways</h3>
  <ul>
    <li>Takeaway one.</li>
    <li>Takeaway two.</li>
    <li>Takeaway three.</li>
  </ul>
</div>
```

FAQ section (when there are clear questions/answers in the content, OR when the topic naturally invites questions):
```html
<div class="blog-faq">
  <h2>Frequently Asked Questions</h2>
  <details class="blog-faq-item">
    <summary>Question goes here?</summary>
    <div class="faq-answer">
      <p>Answer paragraph.</p>
    </div>
  </details>
  <details class="blog-faq-item">
    <summary>Another question?</summary>
    <div class="faq-answer">
      <p>Answer.</p>
    </div>
  </details>
</div>
```

CTA card (REQUIRED at the very end of every post — replace any "schedule a call / book a session / take action" CTA from the original content with this):
```html
<div class="blog-cta-card">
  <h3>Compelling CTA Headline (5-8 words)</h3>
  <p>1-2 sentence pitch tailored to the article topic — what they'll get and why now.</p>
  <a href="../contact.html" class="btn btn-gold">Schedule a Free Call</a>
</div>
```

If the original mentions the "5-Day Mindset Awareness Challenge", make the CTA about that instead:
```html
<div class="blog-cta-card">
  <h3>Ready to Build Real Mental Awareness?</h3>
  <p>Take the free 5-Day Mindset Awareness Challenge and start building the mental systems that drive lasting success.</p>
  <a href="../index.html#challenge" class="btn btn-gold">Start the Free Challenge</a>
</div>
```

**3. SEO best practices:**
- Use natural language and primary keyword variations in H2s
- Each section should have ~100-200 words
- Keep paragraphs short (2-4 sentences)
- Use bold (`<strong>`) for key phrases readers might scan for
- Use `<em>` sparingly for emphasis

**4. Voice & tone:**
- Keep Shawn's authentic coaching voice
- Direct, motivational, action-oriented
- Don't add fluff or filler

**5. CRITICAL rules:**
- Preserve ALL meaningful content from the original
- Don't invent statistics, names, or facts
- Don't change the core message
- Output ONLY the HTML body (no `<html>`, `<head>`, `<article>`, `<body>` tags — just the inner content that goes inside `<div class="blog-article-body">`)
- Don't include the H1 (it's already in the page header)
- Use `class="..."` not `class='...'`
- Make sure all tags are properly closed

# THE BLOG POST

**Title:** {title}

**Original body content (messy):**
```
{body}
```

Now output the clean, restructured HTML body. Start directly with the first paragraph or component — no preamble, no markdown, no code fences."""


def call_claude(title, body, max_retries=3):
    """Call Claude API to enhance one blog post"""
    prompt = ENHANCEMENT_PROMPT.format(title=title, body=body)

    payload = {
        'model': MODEL,
        'max_tokens': 8000,
        'messages': [{'role': 'user', 'content': prompt}],
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=data,
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result['content'][0]['text']
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            print(f"  ! API error {e.code} (attempt {attempt+1}): {err_body[:200]}")
            if e.code == 529 or e.code == 429:  # Overloaded / rate limit
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except Exception as e:
            print(f"  ! Network error (attempt {attempt+1}): {e}")
            time.sleep(3)
            continue
    raise RuntimeError("Max retries exceeded")


def extract_body(html):
    """Extract content between <div class="blog-article-body"> and the next </div> followed by author box"""
    # Use a careful regex - match the opening div and capture until we hit the </div> followed by blog-author-box
    pattern = r'<div class="blog-article-body">(.*?)</div>\s*\n*\s*<div class="blog-author-box">'
    m = re.search(pattern, html, re.DOTALL)
    if not m:
        return None
    return m.group(1).strip()


def replace_body(html, new_body):
    """Replace the body content while preserving the rest"""
    pattern = r'(<div class="blog-article-body">)(.*?)(</div>\s*\n*\s*<div class="blog-author-box">)'
    indented_body = '\n          ' + new_body.strip() + '\n        '
    replacement = r'\1' + indented_body + r'\3'
    return re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)


def get_title(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return ''


def process_post(filepath):
    """Process one blog post"""
    filename = os.path.basename(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Skip if already enhanced (has callout, blog-cta-card, or blog-step components)
    if 'class="blog-cta-card"' in html or 'class="callout callout' in html:
        return filename, 'SKIP - already enhanced', None

    title = get_title(html)
    body = extract_body(html)

    if not body or len(body) < 100:
        return filename, 'SKIP - body too short', None

    try:
        new_body = call_claude(title, body)
        # Strip any code fences if Claude included them
        new_body = re.sub(r'^```(?:html)?\n', '', new_body.strip())
        new_body = re.sub(r'\n```$', '', new_body.strip())

        new_html = replace_body(html, new_body)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_html)

        return filename, 'OK', len(new_body)
    except Exception as e:
        return filename, f'ERROR: {e}', None


def main():
    args = sys.argv[1:]
    if args and args[0] == '--test':
        # Test mode: process only 2 posts
        files = sorted(glob.glob(os.path.join(BLOG_DIR, '*.html')))[:2]
    elif args and args[0] == '--file':
        files = [os.path.join(BLOG_DIR, args[1])]
    else:
        files = sorted(glob.glob(os.path.join(BLOG_DIR, '*.html')))

    print(f"Processing {len(files)} blog posts with {MODEL}...")
    print(f"Concurrency: 4 parallel")

    success = 0
    failed = 0
    skipped = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_post, f): f for f in files}
        for i, future in enumerate(as_completed(futures), 1):
            filename, status, size = future.result()
            if status == 'OK':
                success += 1
                print(f"  [{i}/{len(files)}] ✓ {filename} ({size} chars)")
            elif status.startswith('SKIP'):
                skipped += 1
                print(f"  [{i}/{len(files)}] ⊘ {filename} - {status}")
            else:
                failed += 1
                print(f"  [{i}/{len(files)}] ✗ {filename} - {status}")

    print(f"\n{'='*60}")
    print(f"Done! Success: {success}, Failed: {failed}, Skipped: {skipped}")


if __name__ == '__main__':
    main()
