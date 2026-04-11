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
        if (challengeForm.querySelector('[name="_honey"]')?.value) return;

        const btn = challengeForm.querySelector('[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Sending...';

        try {
          if (typeof grecaptcha !== 'undefined') {
            try {
              const token = await grecaptcha.execute('6Lck8aQsAAAAAlMA-T6nwfkSf7bv4K-mOhkszeKh', { action: 'challenge_download' });
              const tokenField = challengeForm.querySelector('[name="recaptcha_token"]');
              if (tokenField) tokenField.value = token;
            } catch (err) { console.warn('reCAPTCHA error:', err); }
          }

          const formData = new FormData(challengeForm);
          const data = Object.fromEntries(formData.entries());

          fetch('https://myaieditor.com/api/form-notify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
        } catch (err) { console.error('Challenge form error:', err); }

        // Show success + open PDF
        challengeForm.querySelector('.form-fields').style.display = 'none';
        challengeForm.querySelector('.form-success').classList.add('show');
        window.open('ebooks/5-Day Mindset Awareness Challenge-Filled-in (1).pdf', '_blank');
      });
    }
  }

  // Form submission via form-notify
  document.querySelectorAll('form[data-ajax]').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Honeypot check
      if (form.querySelector('[name="_honey"]')?.value) return;

      const btn = form.querySelector('[type="submit"]');
      const originalText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Sending...';

      try {
        // Get reCAPTCHA v3 token
        if (typeof grecaptcha !== 'undefined') {
          try {
            const token = await grecaptcha.execute('6Lck8aQsAAAAAlMA-T6nwfkSf7bv4K-mOhkszeKh', { action: 'form_submit' });
            const tokenField = form.querySelector('[name="recaptcha_token"]');
            if (tokenField) tokenField.value = token;
          } catch (err) {
            console.warn('reCAPTCHA error:', err);
          }
        }

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        await fetch('https://myaieditor.com/api/form-notify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      } catch (err) {
        console.error('Form submit error:', err);
      }

      // Show thank you
      const fields = form.querySelector('.form-fields');
      const success = form.querySelector('.form-success');
      if (fields) fields.style.display = 'none';
      if (success) success.classList.add('show');
    });
  });
});
