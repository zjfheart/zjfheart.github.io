(() => {
  const header = document.querySelector('[data-header]');
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-nav]');

  const updateHeader = () => header?.classList.toggle('is-scrolled', window.scrollY > 12);
  updateHeader();
  window.addEventListener('scroll', updateHeader, { passive: true });

  if (toggle && nav) {
    const closeMenu = () => {
      toggle.setAttribute('aria-expanded', 'false');
      nav.classList.remove('is-open');
    };

    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    });
    nav.addEventListener('click', event => {
      if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeMenu();
    });
    window.addEventListener('resize', () => {
      if (window.innerWidth > 1050) closeMenu();
    });
  }

  const verticalScrollRegions = [...document.querySelectorAll('[data-vertical-scroll]')];
  const sizeVerticalScrollRegions = () => {
    verticalScrollRegions.forEach(region => {
      const visibleItems = Number.parseInt(region.dataset.visibleItems || '5', 10);
      const items = [...region.children].slice(0, visibleItems);
      if (!items.length) return;
      const visibleHeight = items.reduce((total, item) => total + item.getBoundingClientRect().height, 0);
      region.style.setProperty('--experience-window-height', `${Math.ceil(visibleHeight + 1)}px`);
    });
  };

  let verticalResizeFrame = 0;
  const scheduleVerticalResize = () => {
    window.cancelAnimationFrame(verticalResizeFrame);
    verticalResizeFrame = window.requestAnimationFrame(sizeVerticalScrollRegions);
  };
  scheduleVerticalResize();
  document.fonts?.ready.then(scheduleVerticalResize);
  window.addEventListener('resize', scheduleVerticalResize);
  if ('ResizeObserver' in window) {
    const experienceResizeObserver = new ResizeObserver(scheduleVerticalResize);
    verticalScrollRegions.forEach(region => {
      [...region.children].slice(0, Number.parseInt(region.dataset.visibleItems || '5', 10)).forEach(item => experienceResizeObserver.observe(item));
    });
  }

  document.querySelectorAll('[data-carousel-group]').forEach(group => {
    const carousel = group.querySelector('[data-carousel]');
    const previous = group.querySelector('[data-carousel-prev]');
    const next = group.querySelector('[data-carousel-next]');
    if (!carousel || !previous || !next) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const cardStep = () => {
      const card = carousel.querySelector('.credential-card');
      const gap = Number.parseFloat(window.getComputedStyle(carousel).columnGap) || 0;
      return card ? card.getBoundingClientRect().width + gap : carousel.clientWidth;
    };
    const updateControls = () => {
      const maximum = Math.max(0, carousel.scrollWidth - carousel.clientWidth);
      previous.disabled = carousel.scrollLeft <= 2;
      next.disabled = carousel.scrollLeft >= maximum - 2;
    };
    const move = direction => carousel.scrollBy({
      left: direction * cardStep(),
      behavior: prefersReducedMotion.matches ? 'auto' : 'smooth'
    });

    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    carousel.addEventListener('scroll', updateControls, { passive: true });
    carousel.addEventListener('keydown', event => {
      if (event.target !== carousel) return;
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        move(-1);
      }
      if (event.key === 'ArrowRight') {
        event.preventDefault();
        move(1);
      }
      if (event.key === 'Home') {
        event.preventDefault();
        carousel.scrollTo({ left: 0, behavior: prefersReducedMotion.matches ? 'auto' : 'smooth' });
      }
      if (event.key === 'End') {
        event.preventDefault();
        carousel.scrollTo({ left: carousel.scrollWidth, behavior: prefersReducedMotion.matches ? 'auto' : 'smooth' });
      }
    });
    window.addEventListener('resize', updateControls);
    updateControls();
  });

  const tablist = document.querySelector('[data-year-tabs]');
  if (!tablist) return;

  const tabs = [...tablist.querySelectorAll('[role="tab"]')];
  const panels = [...document.querySelectorAll('[data-publication-panel]')];
  const years = new Set(tabs.map(tab => tab.dataset.year));

  const activateYear = (year, updateUrl = true) => {
    if (!years.has(year)) return;
    tabs.forEach(tab => {
      const active = tab.dataset.year === year;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active) tab.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    });
    panels.forEach(panel => {
      panel.hidden = panel.dataset.publicationPanel !== year;
    });
    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set('year', year);
      url.hash = 'publications';
      window.history.replaceState({}, '', url);
    }
  };

  const requestedYear = new URL(window.location.href).searchParams.get('year');
  if (requestedYear && years.has(requestedYear)) activateYear(requestedYear, false);

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activateYear(tab.dataset.year));
    tab.addEventListener('keydown', event => {
      let nextIndex = null;
      if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') nextIndex = 0;
      if (event.key === 'End') nextIndex = tabs.length - 1;
      if (nextIndex === null) return;
      event.preventDefault();
      tabs[nextIndex].focus();
      activateYear(tabs[nextIndex].dataset.year);
    });
  });
})();
