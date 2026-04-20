#!/usr/bin/env python3
"""
Add GTM, Google Consent Mode, and reCAPTCHA to all pages.
Also add reCAPTCHA to pages with forms that are missing it.
"""
import os, re, glob

SITE_DIR = os.path.join(os.path.dirname(__file__), '..')
GTM_ID = 'GTM-5LVJJFV'
RECAPTCHA_KEY = '6Lck8aQsAAAAAlMA-T6nwfkSf7bv4K-mOhkszeKh'

# Consent Mode + GTM head script
CONSENT_AND_GTM_HEAD = f'''  <!-- Google Consent Mode v2 -->
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
  }})(window,document,'script','dataLayer','{GTM_ID}');</script>
  <!-- End Google Tag Manager -->'''

# GTM noscript (after <body>)
GTM_NOSCRIPT = f'''  <!-- Google Tag Manager (noscript) -->
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
  height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
  <!-- End Google Tag Manager (noscript) -->'''

RECAPTCHA_SCRIPT = f'  <script src="https://www.google.com/recaptcha/api.js?render={RECAPTCHA_KEY}"></script>'

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    filename = os.path.basename(filepath)
    changes = []

    # Skip if GTM already present
    if 'googletagmanager.com/gtm.js' in content:
        return changes

    # Add Consent Mode + GTM head script before </head>
    if '</head>' in content:
        content = content.replace('</head>', CONSENT_AND_GTM_HEAD + '\n</head>')
        changes.append('Added Consent Mode + GTM head script')

    # Add GTM noscript after <body> (or <body ...>)
    body_match = re.search(r'<body[^>]*>', content)
    if body_match:
        insert_pos = body_match.end()
        content = content[:insert_pos] + '\n' + GTM_NOSCRIPT + '\n' + content[insert_pos:]
        changes.append('Added GTM noscript')

    # Add reCAPTCHA to pages with forms that don't have it
    has_form = 'data-ajax' in content or 'data-challenge' in content
    has_recaptcha = 'recaptcha/api.js' in content
    if has_form and not has_recaptcha:
        content = content.replace('</head>', RECAPTCHA_SCRIPT + '\n</head>')
        changes.append('Added reCAPTCHA v3 script')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return changes

# Process root HTML files
print("Processing root HTML files...")
root_files = glob.glob(os.path.join(SITE_DIR, '*.html'))
for f in sorted(root_files):
    changes = process_file(f)
    if changes:
        print(f"  {os.path.basename(f)}: {', '.join(changes)}")
    else:
        print(f"  {os.path.basename(f)}: (skipped - already has GTM)")

# Process blog HTML files
print("\nProcessing blog HTML files...")
blog_files = glob.glob(os.path.join(SITE_DIR, 'blog', '*.html'))
for f in sorted(blog_files):
    changes = process_file(f)
    if changes:
        print(f"  {os.path.basename(f)}: {', '.join(changes)}")

print(f"\nDone! Processed {len(root_files)} root + {len(blog_files)} blog files.")
