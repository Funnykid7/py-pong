// ─── SMOOTH SCROLL ─────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const href = a.getAttribute('href');
    if (href === '#') return;
    const target = document.querySelector(href);
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth' });
    document.getElementById('nav-overlay').classList.remove('open');
  });
});

// ─── HAMBURGER MENU ────────────────────────────────────────
const navToggle  = document.getElementById('nav-toggle');
const navOverlay = document.getElementById('nav-overlay');
const navClose   = document.getElementById('nav-overlay-close');

navToggle.addEventListener('click', () => navOverlay.classList.add('open'));
navClose.addEventListener('click',  () => navOverlay.classList.remove('open'));

navOverlay.querySelectorAll('.nav-overlay-link').forEach(link => {
  link.addEventListener('click', () => navOverlay.classList.remove('open'));
});

// ─── ACTIVE NAV LINK ───────────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link[data-section]');

const navObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(l => l.classList.remove('active'));
      const active = document.querySelector(`.nav-link[data-section="${entry.target.id}"]`);
      if (active) active.classList.add('active');
    }
  });
}, { threshold: 0.4 });

sections.forEach(s => navObserver.observe(s));

// ─── SCROLL REVEAL ─────────────────────────────────────────
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (!prefersReduced) {
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.reveal-child').forEach(el => {
    revealObserver.observe(el);
  });
} else {
  document.querySelectorAll('.reveal-child').forEach(el => {
    el.classList.add('visible');
  });
}
