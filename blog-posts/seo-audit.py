#!/usr/bin/env python3
"""
Deep SEO audit — checks every HTML page for issues.
"""
import os, re, glob, json
from collections import defaultdict

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def extract_tag(html, tag_name, attr=None):
    """Extract a meta/title tag value"""
    if tag_name == 'title':
        m = re.search(r'<title>([^<]+)</title>', html)
        return m.group(1).strip() if m else None
    if tag_name == 'h1':
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if m:
            return re.sub(r'<[^>]+>', '', m.group(1)).strip()
        return None
    if tag_name == 'meta_description':
        m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', html)
        return m.group(1) if m else None
    if tag_name == 'canonical':
        m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html)
        return m.group(1) if m else None
    if tag_name == 'og_image':
        m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html)
        return m.group(1) if m else None
    if tag_name == 'og_title':
        m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html)
        return m.group(1) if m else None
    return None

def extract_schema(html):
    """Extract all JSON-LD schema types"""
    types = []
    errors = []
    for m in re.finditer(r'<script type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL):
        block = m.group(1).strip()
        try:
            data = json.loads(block)
            if isinstance(data, dict):
                t = data.get('@type', 'Unknown')
                types.append(t)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        types.append(item.get('@type', 'Unknown'))
        except json.JSONDecodeError as e:
            errors.append(str(e)[:100])
    return types, errors

def check_images(html):
    """Check all img tags for alt, width, height"""
    issues = []
    for m in re.finditer(r'<img\s+([^>]+)>', html):
        attrs = m.group(1)
        if 'alt=' not in attrs:
            issues.append('missing-alt')
        if 'width=' not in attrs or 'height=' not in attrs:
            # Don't flag decorative icons like social logos
            if 'class="fab' not in attrs and 'class="fas' not in attrs:
                issues.append('missing-dimensions')
    return issues

def audit_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    rel = os.path.relpath(filepath, SITE_DIR)
    result = {
        'path': rel,
        'title': extract_tag(html, 'title'),
        'description': extract_tag(html, 'meta_description'),
        'canonical': extract_tag(html, 'canonical'),
        'h1': extract_tag(html, 'h1'),
        'og_title': extract_tag(html, 'og_title'),
        'og_image': extract_tag(html, 'og_image'),
    }
    result['schema_types'], result['schema_errors'] = extract_schema(html)
    result['image_issues'] = check_images(html)

    result['h1_count'] = len(re.findall(r'<h1[^>]*>', html))
    result['has_gtm'] = 'googletagmanager.com/gtm.js' in html
    result['has_consent'] = "gtag('consent'" in html
    result['has_recaptcha'] = 'recaptcha/api.js' in html
    result['has_form'] = 'data-ajax' in html or 'data-challenge' in html
    result['external_unsafe'] = len(re.findall(r'target="_blank"(?![^>]*rel="[^"]*noopener)', html))

    # Check for Duda references
    result['duda_refs'] = len(re.findall(r'irp\.cdn-website\.com|googleusercontent\.com/d/', html))

    return result

# Collect all HTML files
root_files = sorted(glob.glob(os.path.join(SITE_DIR, '*.html')))
blog_files = sorted(glob.glob(os.path.join(SITE_DIR, 'blog', '*.html')))

print("="*80)
print("SEO AUDIT REPORT — Shawn Huber Site")
print("="*80)

all_results = []
for f in root_files + blog_files:
    all_results.append(audit_file(f))

# Detect duplicates
title_dupes = defaultdict(list)
desc_dupes = defaultdict(list)
canonical_dupes = defaultdict(list)
for r in all_results:
    if r['title']: title_dupes[r['title']].append(r['path'])
    if r['description']: desc_dupes[r['description']].append(r['path'])
    if r['canonical']: canonical_dupes[r['canonical']].append(r['path'])

# ── SUMMARY ──
print(f"\n📊 SUMMARY")
print(f"Total pages audited: {len(all_results)} ({len(root_files)} root + {len(blog_files)} blog)")
gtm_count = sum(1 for r in all_results if r['has_gtm'])
consent_count = sum(1 for r in all_results if r['has_consent'])
print(f"Pages with GTM: {gtm_count}/{len(all_results)}")
print(f"Pages with Consent Mode: {consent_count}/{len(all_results)}")

form_pages = [r for r in all_results if r['has_form']]
print(f"Form pages: {len(form_pages)}, all with reCAPTCHA: {all(r['has_recaptcha'] for r in form_pages)}")

# ── CRITICAL ISSUES ──
print(f"\n🔴 CRITICAL ISSUES")

dup_titles = {k: v for k, v in title_dupes.items() if len(v) > 1}
if dup_titles:
    print(f"\nDuplicate titles ({len(dup_titles)}):")
    for title, files in list(dup_titles.items())[:5]:
        print(f"  '{title[:60]}...' used in {len(files)} files")
else:
    print("  ✓ No duplicate titles")

dup_desc = {k: v for k, v in desc_dupes.items() if len(v) > 1}
if dup_desc:
    print(f"\nDuplicate descriptions ({len(dup_desc)}):")
    for desc, files in list(dup_desc.items())[:5]:
        print(f"  '{desc[:60]}...' used in {len(files)} files")
else:
    print("  ✓ No duplicate descriptions")

dup_canon = {k: v for k, v in canonical_dupes.items() if len(v) > 1}
if dup_canon:
    print(f"\nDuplicate canonicals ({len(dup_canon)}):")
    for canon, files in list(dup_canon.items())[:5]:
        print(f"  {canon} used in {len(files)} files: {files}")
else:
    print("  ✓ No duplicate canonicals")

schema_errors = [r for r in all_results if r['schema_errors']]
if schema_errors:
    print(f"\nSchema JSON errors ({len(schema_errors)}):")
    for r in schema_errors[:5]:
        print(f"  {r['path']}: {r['schema_errors']}")
else:
    print("  ✓ All JSON-LD schema blocks valid")

missing_h1 = [r for r in all_results if r['h1_count'] != 1]
if missing_h1:
    print(f"\nH1 count issues ({len(missing_h1)}):")
    for r in missing_h1[:10]:
        print(f"  {r['path']}: {r['h1_count']} h1 tags")
else:
    print("  ✓ Every page has exactly one H1")

missing_canonical = [r for r in all_results if not r['canonical']]
if missing_canonical:
    print(f"\nMissing canonical ({len(missing_canonical)}):")
    for r in missing_canonical[:5]:
        print(f"  {r['path']}")
else:
    print("  ✓ All pages have canonical")

missing_og_image = [r for r in all_results if not r['og_image']]
if missing_og_image:
    print(f"\nMissing og:image ({len(missing_og_image)}):")
    for r in missing_og_image[:5]:
        print(f"  {r['path']}")

# ── WARNINGS ──
print(f"\n⚠️  WARNINGS")

# Title length
bad_titles = [r for r in all_results if r['title'] and (len(r['title']) < 30 or len(r['title']) > 65)]
if bad_titles:
    print(f"\nTitle length issues (should be 30-65 chars) ({len(bad_titles)}):")
    for r in bad_titles[:10]:
        print(f"  {r['path']} [{len(r['title'])}]: {r['title'][:70]}")

# Description length
bad_desc = [r for r in all_results if r['description'] and (len(r['description']) < 120 or len(r['description']) > 170)]
if bad_desc:
    print(f"\nDescription length issues (should be 120-170 chars) ({len(bad_desc)}):")
    for r in bad_desc[:10]:
        print(f"  {r['path']} [{len(r['description'])}]: {r['description'][:70]}")

missing_desc = [r for r in all_results if not r['description']]
if missing_desc:
    print(f"\nMissing description ({len(missing_desc)}):")
    for r in missing_desc[:5]:
        print(f"  {r['path']}")

# External unsafe links
unsafe_links = [r for r in all_results if r['external_unsafe'] > 0]
if unsafe_links:
    print(f"\ntarget=_blank missing rel=noopener ({len(unsafe_links)}):")
    for r in unsafe_links[:5]:
        print(f"  {r['path']}: {r['external_unsafe']} unsafe links")
else:
    print("\n  ✓ All external links have rel=noopener noreferrer")

# Image issues
image_problems = [r for r in all_results if r['image_issues']]
if image_problems:
    missing_alt = sum(r['image_issues'].count('missing-alt') for r in image_problems)
    missing_dim = sum(r['image_issues'].count('missing-dimensions') for r in image_problems)
    print(f"\nImage issues: {missing_alt} missing alt, {missing_dim} missing dimensions")
    print(f"  Most affected files:")
    image_problems.sort(key=lambda r: len(r['image_issues']), reverse=True)
    for r in image_problems[:5]:
        print(f"    {r['path']}: {len(r['image_issues'])} issues")

# Duda refs (should be zero now)
duda_refs = [r for r in all_results if r['duda_refs'] > 0]
if duda_refs:
    print(f"\n❌ DUDA REFERENCES STILL PRESENT ({len(duda_refs)} files):")
    for r in duda_refs[:10]:
        print(f"  {r['path']}: {r['duda_refs']} refs")
else:
    print("\n  ✓ Zero Duda/external image references")

# ── SCHEMA COVERAGE ──
print(f"\n📋 SCHEMA COVERAGE")
schema_counts = defaultdict(int)
for r in all_results:
    for t in r['schema_types']:
        schema_counts[t] += 1
for t, c in sorted(schema_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c} pages")

print(f"\n" + "="*80)
