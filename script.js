// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggle && navLinks) {
    toggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      toggle.classList.toggle('active');
    });

    // Close mobile nav on link click
    navLinks.querySelectorAll('a:not(.dropdown-trigger)').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        toggle.classList.remove('active');
      });
    });

    // Mobile dropdown toggle
    navLinks.querySelectorAll('.dropdown-trigger').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024) {
          e.preventDefault();
          trigger.parentElement.classList.toggle('open');
        }
      });
    });
  }

  // Nav scroll effect
  const nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 20);
    });
  }

  // Scroll to top button
  const scrollBtn = document.querySelector('.scroll-top');
  if (scrollBtn) {
    window.addEventListener('scroll', () => {
      scrollBtn.classList.toggle('visible', window.scrollY > 400);
    });
    scrollBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Fade-up animations on scroll
  const fadeEls = document.querySelectorAll('.fade-up');
  if (fadeEls.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    fadeEls.forEach(el => observer.observe(el));
  }

  // Accordion functionality
  document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const body = item.querySelector('.accordion-body');
      const isOpen = item.classList.contains('open');

      // Close all
      document.querySelectorAll('.accordion-item').forEach(ai => {
        ai.classList.remove('open');
        ai.querySelector('.accordion-body').style.maxHeight = null;
      });

      if (!isOpen) {
        item.classList.add('open');
        body.style.maxHeight = body.scrollHeight + 'px';
      }
    });
  });

  // Inject anti-bot timestamp into all forms (server rejects submissions < 2s)
  document.querySelectorAll('form[data-ajax], form[data-challenge]').forEach(form => {
    let ts = form.querySelector('[name="_ts"]');
    if (!ts) {
      ts = document.createElement('input');
      ts.type = 'hidden';
      ts.name = '_ts';
      form.appendChild(ts);
    }
    ts.value = Date.now();
  });

  // Challenge Modal
  const challengeModal = document.getElementById('challengeModal');
  if (challengeModal) {
    const openModal = () => { challengeModal.classList.add('open'); document.body.style.overflow = 'hidden'; };
    const closeModal = () => { challengeModal.classList.remove('open'); document.body.style.overflow = ''; };

    document.querySelectorAll('[data-open-challenge]').forEach(btn => {
      btn.addEventListener('click', (e) => { e.preventDefault(); openModal(); });
    });

    challengeModal.querySelector('.modal-close').addEventListener('click', closeModal);
    challengeModal.addEventListener('click', (e) => { if (e.target === challengeModal) closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && challengeModal.classList.contains('open')) closeModal(); });

    // Challenge form submit
    const challengeForm = challengeModal.querySelector('form[data-challenge]');
    if (challengeForm) {
      challengeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        // Honeypot — ONLY _honey (see note on the main handler below)
        if (challengeForm.querySelector('[name="_honey"]')?.value) return;

        // Name + email are required to receive the PDF
        if (!validateContactFields(challengeForm)) return;

        const btn = challengeForm.querySelector('[type="submit"]');
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Sending...';

        let accepted = false;
        try {
          if (typeof grecaptcha !== 'undefined') {
            try {
              const token = await grecaptcha.execute('6Lck8aQsAAAAALMA-T6nwfkSf7bv4K-mOhkszeKh', { action: 'challenge_download' });
              const tokenField = challengeForm.querySelector('[name="recaptcha_token"]');
              if (tokenField) tokenField.value = token;
            } catch (err) { console.warn('reCAPTCHA error:', err); }
          }

          const formData = new FormData(challengeForm);
          const data = Object.fromEntries(formData.entries());

          const res = await fetch('https://myaieditor.com/api/form-notify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          accepted = res.ok;
        } catch (err) { console.error('Challenge form error:', err); }

        if (accepted) {
          challengeForm.querySelector('.form-fields').style.display = 'none';
          challengeForm.querySelector('.form-success').classList.add('show');
          window.open('ebooks/5-Day Mental Wellness Reset.pdf', '_blank');
        } else {
          btn.disabled = false;
          btn.textContent = originalText;
          showFormError(challengeForm, "Sorry — that didn't go through. Please try again or call us at (919) 824-3530.");
        }
      });
    }
  }

  // Form submission via form-notify
  document.querySelectorAll('form[data-ajax]').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Honeypot check — ONLY _honey. Never trap on a real-sounding field name
      // (website/company/url/phone): browsers autofill those for REAL visitors and
      // form-notify then silently discards a genuine lead.
      if (form.querySelector('[name="_honey"]')?.value) return;

      // Require a name and an email before we'll send anything.
      // Backs up the HTML `required` attributes, which don't apply to this
      // JS submit path in every browser/edge case.
      if (!validateContactFields(form)) return;

      const btn = form.querySelector('[type="submit"]');
      const originalText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Sending...';

      let accepted = false;
      try {
        // Get reCAPTCHA v3 token
        if (typeof grecaptcha !== 'undefined') {
          try {
            const token = await grecaptcha.execute('6Lck8aQsAAAAALMA-T6nwfkSf7bv4K-mOhkszeKh', { action: 'form_submit' });
            const tokenField = form.querySelector('[name="recaptcha_token"]');
            if (tokenField) tokenField.value = token;
          } catch (err) {
            console.warn('reCAPTCHA error:', err);
          }
        }

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('https://myaieditor.com/api/form-notify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        accepted = res.ok;
      } catch (err) {
        console.error('Form submit error:', err);
      }

      // Only claim success if the server actually took it. Showing a thank-you
      // regardless is how a total form outage stays invisible for months.
      if (accepted) {
        const fields = form.querySelector('.form-fields');
        const success = form.querySelector('.form-success');
        if (fields) fields.style.display = 'none';
        if (success) success.classList.add('show');
      } else {
        btn.disabled = false;
        btn.textContent = originalText;
        showFormError(form, "Sorry — that didn't go through. Please try again or call us at (919) 824-3530.");
      }
    });
  });
});

// ── Form helpers ──────────────────────────────────────────────────────────
// Require a name and a valid email. Returns true when OK, otherwise focuses
// the first bad field and shows an inline message.
function validateContactFields(form) {
  const nameEl = form.querySelector('[name="first_name"], [name="name"], [name="full_name"]');
  const emailEl = form.querySelector('[name="email"]');

  if (nameEl && !nameEl.value.trim()) {
    showFormError(form, 'Please enter your name so we know who to reach out to.');
    nameEl.focus();
    return false;
  }
  const email = emailEl ? emailEl.value.trim() : '';
  if (emailEl && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    showFormError(form, 'Please enter a valid email address so we can get back to you.');
    emailEl.focus();
    return false;
  }
  clearFormError(form);
  return true;
}

function showFormError(form, message) {
  let el = form.querySelector('.form-error');
  if (!el) {
    el = document.createElement('p');
    el.className = 'form-error';
    el.setAttribute('role', 'alert');
    const fields = form.querySelector('.form-fields') || form;
    fields.appendChild(el);
  }
  el.textContent = message;
  el.style.display = 'block';
}

function clearFormError(form) {
  const el = form.querySelector('.form-error');
  if (el) el.style.display = 'none';
}
