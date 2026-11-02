/**
 * Clipeus Virtutis - Shared Global Trade System & Turbo Navigation Engine
 * Synchronizes inquiry docket, sample requests, and instant animated page transitions
 */

const CV_TRADE = {
  getDocket: function() {
    try {
      const saved = localStorage.getItem('cv_rfq_docket');
      return saved ? JSON.parse(saved) : [];
    } catch(e) {
      return [];
    }
  },

  saveDocket: function(items) {
    try {
      localStorage.setItem('cv_rfq_docket', JSON.stringify(items));
    } catch(e) {}
    CV_TRADE.renderDocketUI();
  },

  addToDocket: function(productTitle, sku) {
    const docket = CV_TRADE.getDocket();
    const itemLabel = sku ? `${productTitle} (${sku})` : productTitle;
    if (!docket.includes(itemLabel)) {
      docket.push(itemLabel);
      CV_TRADE.saveDocket(docket);
    }
    CV_TRADE.openDrawer();
  },

  addSampleKit: function(productTitle, sku) {
    const sampleLabel = `[Sample Kit] ${productTitle} (${sku || 'LAB-SPL'})`;
    const docket = CV_TRADE.getDocket();
    if (!docket.includes(sampleLabel)) {
      docket.push(sampleLabel);
      CV_TRADE.saveDocket(docket);
    }
    const sampleCb = document.getElementById('drawer-sample');
    if (sampleCb) sampleCb.checked = true;
    CV_TRADE.openDrawer();
  },

  removeFromDocket: function(index) {
    const docket = CV_TRADE.getDocket();
    docket.splice(index, 1);
    CV_TRADE.saveDocket(docket);
  },

  clearDocket: function() {
    CV_TRADE.saveDocket([]);
  },

  renderDocketUI: function() {
    const docket = CV_TRADE.getDocket();
    const badges = document.querySelectorAll('.cv-docket-count');
    badges.forEach(b => {
      b.textContent = docket.length;
    });

    const listContainer = document.getElementById('drawer-docket-list');
    const emptyState = document.getElementById('drawer-docket-empty');
    const totalCountText = document.getElementById('drawer-docket-total');
    const hiddenItemsInput = document.getElementById('drawer-docket-input');

    if (totalCountText) {
      totalCountText.textContent = `${docket.length} Item${docket.length === 1 ? '' : 's'}`;
    }

    if (hiddenItemsInput) {
      hiddenItemsInput.value = docket.join('; ');
    }

    if (!listContainer || !emptyState) return;

    if (docket.length === 0) {
      listContainer.classList.add('hidden');
      emptyState.classList.remove('hidden');
      listContainer.innerHTML = '';
    } else {
      emptyState.classList.add('hidden');
      listContainer.classList.remove('hidden');
      listContainer.innerHTML = docket.map((item, idx) => `
        <div class="flex items-center justify-between p-2.5 rounded-xl bg-white border border-stone-200 text-xs shadow-sm">
          <div class="flex items-center gap-2 pr-2">
            <span class="w-1.5 h-1.5 rounded-full ${item.startsWith('[Sample') ? 'bg-amber-600' : 'bg-emerald-600'} flex-shrink-0"></span>
            <span class="font-medium text-stone-900">${item}</span>
          </div>
          <button type="button" onclick="CV_TRADE.removeFromDocket(${idx})" class="text-rose-500 hover:text-rose-700 font-bold px-2 py-0.5 rounded text-xs transition-colors" title="Remove">✕</button>
        </div>
      `).join('');
    }
  },

  openDrawer: function() {
    const backdrop = document.getElementById('rfq-drawer-backdrop');
    const drawer = document.getElementById('rfq-drawer');
    if (backdrop && drawer) {
      backdrop.classList.remove('hidden');
      setTimeout(() => backdrop.classList.remove('opacity-0'), 10);
      drawer.classList.remove('translate-x-full');
    }
    CV_TRADE.renderDocketUI();
  },

  closeDrawer: function() {
    const backdrop = document.getElementById('rfq-drawer-backdrop');
    const drawer = document.getElementById('rfq-drawer');
    if (backdrop && drawer) {
      backdrop.classList.add('opacity-0');
      drawer.classList.add('translate-x-full');
      setTimeout(() => backdrop.classList.add('hidden'), 300);
    }
  },

  handleDrawerSubmit: function(event) {
    event.preventDefault();
    const docket = CV_TRADE.getDocket();
    const company = document.getElementById('drawer-company')?.value || 'Trade Partner';
    const email = document.getElementById('drawer-email')?.value || '';
    const phone = document.getElementById('drawer-phone')?.value || '';
    const volume = document.getElementById('drawer-volume')?.value || 'Commercial Sample / Trial';
    const incoterm = document.getElementById('drawer-incoterm')?.value || 'CIF';
    const port = document.getElementById('drawer-port')?.value || 'Global';
    const sampleReq = document.getElementById('drawer-sample')?.checked;

    const rfqId = `CV-RFQ-2026-${Math.floor(1000 + Math.random() * 9000)}`;

    const form = document.getElementById('drawer-rfq-form');
    const successBox = document.getElementById('drawer-rfq-success');

    if (form && successBox) {
      form.classList.add('hidden');
      successBox.classList.remove('hidden');

      const refEl = document.getElementById('drawer-success-ref');
      const detailEl = document.getElementById('drawer-success-details');
      if (refEl) refEl.textContent = rfqId;
      if (detailEl) {
        detailEl.innerHTML = `
          <strong>${company}</strong>, your formal RFQ inquiry for <strong>${docket.length > 0 ? docket.join(', ') : 'Verified Trade Products'}</strong> has been routed to our Chennai Trade Desk. Formal landed quote under <strong>Incoterms ${incoterm} (${port})</strong> for volume <strong>${volume}</strong>${sampleReq ? ' <em>(with Physical Lab Sample Pack)</em>' : ''} will be delivered to <strong>${email}</strong> within 18-24 hours.
        `;
      }
    }
  },

  resetDrawerForm: function() {
    const form = document.getElementById('drawer-rfq-form');
    const successBox = document.getElementById('drawer-rfq-success');
    if (form && successBox) {
      form.reset();
      form.classList.remove('hidden');
      successBox.classList.add('hidden');
    }
  },

  toggleMobileNav: function(event) {
    if (event) {
      if (typeof event.stopPropagation === 'function') event.stopPropagation();
      if (typeof event.preventDefault === 'function') event.preventDefault();
    }
    const menu = document.getElementById('mobile-nav-menu');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    const btn = document.getElementById('mobile-menu-btn');
    if (!menu) return;

    const isOpen = menu.classList.contains('open');
    if (isOpen) {
      CV_TRADE.closeMobileNav();
    } else {
      menu.classList.add('open');
      if (backdrop) backdrop.classList.add('open');
      document.body.style.overflow = 'hidden';
      if (btn) {
        btn.setAttribute('aria-expanded', 'true');
        btn.innerHTML = `<svg class="w-6 h-6 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>`;
      }
    }
  },

  closeMobileNav: function() {
    const menu = document.getElementById('mobile-nav-menu');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    const btn = document.getElementById('mobile-menu-btn');
    if (menu) menu.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    document.body.style.overflow = '';
    if (btn) {
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = `<svg class="w-6 h-6 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>`;
    }
  },

  toggleBgVideoMute: function() {
    const video = document.getElementById('bg-trade-video') || document.querySelector('video');
    const audio = document.getElementById('bg-trade-audio');
    const btn = document.getElementById('bg-video-mute-btn');
    const label = document.getElementById('bg-video-mute-label');
    const icon = document.getElementById('bg-video-mute-icon');
    if (!video) return;

    const isMuted = video.muted;
    if (isMuted) {
      // Unmute video
      video.muted = false;
      video.defaultMuted = false;
      video.removeAttribute('muted');
      video.volume = 1.0;

      // Web Audio API unlock for Safari / WebKit
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
          if (!window._cvAudioCtx) window._cvAudioCtx = new AudioContext();
          if (window._cvAudioCtx.state === 'suspended') window._cvAudioCtx.resume();
        }
      } catch (e) {}

      // Play video with audio track
      const pVid = video.play();
      if (pVid && typeof pVid.catch === 'function') {
        pVid.catch(function() {});
      }

      // Sync and play standalone audio stream as guaranteed sound channel
      if (audio) {
        audio.muted = false;
        audio.volume = 1.0;
        audio.currentTime = video.currentTime || 0;
        const pAud = audio.play();
        if (pAud && typeof pAud.catch === 'function') {
          pAud.catch(function() {});
        }
      }

      if (label) label.textContent = 'Mute Audio';
      if (icon) icon.textContent = '🔊';
      if (btn) {
        btn.className = 'px-5 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-400 text-xs font-mono font-bold backdrop-blur-md transition-all flex items-center gap-2.5 shadow-[0_0_24px_rgba(16,185,129,0.8)] cursor-pointer';
      }
    } else {
      // Mute video
      video.muted = true;
      video.defaultMuted = true;
      video.setAttribute('muted', '');
      if (audio) {
        audio.pause();
      }

      if (label) label.textContent = 'Unmute Audio';
      if (icon) icon.textContent = '🔇';
      if (btn) {
        btn.className = 'px-5 py-2.5 rounded-full bg-black/80 hover:bg-black text-white border border-white/20 text-xs font-mono font-bold backdrop-blur-md transition-all flex items-center gap-2.5 shadow-lg cursor-pointer';
      }
    }
  }
};


/* =========================================================================
   TURBO NAVIGATION ENGINE: INSTANTANEOUS 15MS PREFETCHING & SILKY PAGE ANIMATIONS
   ========================================================================= */

const CV_NAV = {
  cache: new Map(),
  isNavigating: false,
  progressBar: null,

  init: function() {
    // 1. Create Glowing Top Progress Laser Bar
    if (!document.getElementById('cv-nav-progress-bar')) {
      const bar = document.createElement('div');
      bar.id = 'cv-nav-progress-bar';
      document.body.prepend(bar);
      this.progressBar = bar;
    } else {
      this.progressBar = document.getElementById('cv-nav-progress-bar');
    }

    // 2. Cache current page into memory immediately
    const currentFile = window.location.pathname.split('/').pop() || 'index.html';
    const mainEl = document.getElementById('main-content');
    if (mainEl) {
      CV_NAV.cache.set(currentFile, {
        title: document.title,
        html: mainEl.innerHTML,
        rawDoc: document.documentElement.outerHTML
      });
      if (currentFile === 'index.html') {
        CV_NAV.cache.set('', {
          title: document.title,
          html: mainEl.innerHTML,
          rawDoc: document.documentElement.outerHTML
        });
      }
    }

    // 3. Intercept clicks and mouseover prefetching on all internal links
    this.bindLinks(document);

    // 4. Handle browser Back / Forward history
    window.addEventListener('popstate', () => {
      const target = window.location.pathname.split('/').pop() || 'index.html';
      CV_NAV.navigateTo(target, false);
    });

    // 5. Close mobile navigation when tapping outside
    document.addEventListener('click', (e) => {
      const menu = document.getElementById('mobile-nav-menu');
      const btn = document.getElementById('mobile-menu-btn');
      if (menu && menu.classList.contains('open')) {
        if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {
          CV_TRADE.closeMobileNav();
        }
      }
    });

    document.addEventListener('touchstart', (e) => {
      const menu = document.getElementById('mobile-nav-menu');
      const btn = document.getElementById('mobile-menu-btn');
      if (menu && menu.classList.contains('open')) {
        if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {
          CV_TRADE.closeMobileNav();
        }
      }
    }, { passive: true });

    // 6. Background Prefetch all core dock pages when idle for 0ms navigation
    const prefetchTargets = ['index.html', 'products.html', 'about.html', 'solutions.html', 'services.html', 'partners.html', 'blog.html', 'contact.html'];
    const prefetchWorker = () => {
      prefetchTargets.forEach((target, i) => {
        setTimeout(() => {
          if (target !== currentFile) CV_NAV.prefetch(target);
        }, i * 150);
      });
    };

    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(prefetchWorker);
    } else {
      setTimeout(prefetchWorker, 800);
    }
  },

  prefetch: function(url) {
    const cleanUrl = url.split('#')[0].split('?')[0];
    if (!cleanUrl || CV_NAV.cache.has(cleanUrl)) return;

    fetch(cleanUrl)
      .then(res => {
        if (!res.ok) throw new Error('Network error');
        return res.text();
      })
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const main = doc.getElementById('main-content');
        if (main) {
          CV_NAV.cache.set(cleanUrl, {
            title: doc.title,
            html: main.innerHTML,
            rawDoc: html
          });
        }
      })
      .catch(() => {});
  },

  bindLinks: function(context) {
    const links = (context || document).querySelectorAll('a[href]');
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (!href) return;
      if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:') || href.startsWith('http')) {
        return;
      }

      // Prefetch on pointerenter or touchstart for 0ms instant click response
      link.addEventListener('pointerenter', () => CV_NAV.prefetch(href), { passive: true });
      link.addEventListener('touchstart', () => CV_NAV.prefetch(href), { passive: true });

      // Intercept click for seamless animated page swap
      link.addEventListener('click', (e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // Allow open in new tab
        e.preventDefault();
        CV_NAV.navigateTo(href, true);
      });
    });
  },

  navigateTo: async function(url, pushState = true) {
    if (CV_NAV.isNavigating) return;

    const cleanUrl = url.split('#')[0].split('?')[0] || 'index.html';
    const currentFile = window.location.pathname.split('/').pop() || 'index.html';

    // If clicking same page, smoothly scroll to top
    if (cleanUrl === currentFile || (cleanUrl === 'index.html' && (currentFile === '' || currentFile === 'index.html'))) {
      CV_TRADE.closeMobileNav();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    CV_NAV.isNavigating = true;

    // 1. Start Glowing Laser Progress Bar
    if (CV_NAV.progressBar) {
      CV_NAV.progressBar.classList.add('active');
      CV_NAV.progressBar.style.width = '30%';
      setTimeout(() => {
        if (CV_NAV.progressBar) CV_NAV.progressBar.style.width = '75%';
      }, 40);
    }

    // 2. Start Silky Outgoing Animation on Main Content
    const mainEl = document.getElementById('main-content');
    if (mainEl) {
      mainEl.classList.remove('cv-page-enter');
      mainEl.classList.add('cv-page-exit');
    }

    // 3. Immediately Update Dock Active Highlights
    CV_NAV.updateDockActive(cleanUrl);

    // 4. Close mobile navigation menu
    CV_TRADE.closeMobileNav();

    try {
      let pageData = CV_NAV.cache.get(cleanUrl);
      if (!pageData) {
        // Fetch on-demand if not prefetched
        const res = await fetch(cleanUrl);
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const main = doc.getElementById('main-content');
        if (main) {
          pageData = {
            title: doc.title,
            html: main.innerHTML,
            rawDoc: html
          };
          CV_NAV.cache.set(cleanUrl, pageData);
        } else {
          window.location.href = url;
          return;
        }
      }

      // Wait 120ms for outgoing transition
      await new Promise(r => setTimeout(r, 120));

      // 5. Swap Content & Title
      if (mainEl) {
        mainEl.innerHTML = pageData.html;
        document.title = pageData.title;

        // Instant scroll to top before entering animation
        window.scrollTo({ top: 0, behavior: 'instant' });

        // Trigger Silky Entrance Animation
        mainEl.classList.remove('cv-page-exit');
        mainEl.classList.add('cv-page-enter');

        setTimeout(() => {
          mainEl.classList.remove('cv-page-enter');
        }, 300);
      }

      // 6. Finish Laser Progress Bar
      if (CV_NAV.progressBar) {
        CV_NAV.progressBar.style.width = '100%';
        setTimeout(() => {
          CV_NAV.progressBar.classList.remove('active');
          CV_NAV.progressBar.style.width = '0%';
        }, 220);
      }

      // 7. Update Browser History State
      if (pushState) {
        window.history.pushState(null, pageData.title, url);
      }

      // 8. Bind Links inside newly rendered content
      CV_NAV.bindLinks(mainEl);

      // 9. Re-evaluate and initialize scripts for the destination page
      CV_NAV.runPageScripts(cleanUrl, pageData.rawDoc);

      // 10. Synchronize RFQ Docket
      CV_TRADE.renderDocketUI();

    } catch (err) {
      console.warn('Turbo navigation fallback:', err);
      window.location.href = url;
    } finally {
      CV_NAV.isNavigating = false;
    }
  },

  updateDockActive: function(targetUrl) {
    const norm = targetUrl === '' ? 'index.html' : targetUrl;
    
    // Update desktop dock links
    const dockLinks = document.querySelectorAll('.nav-pill-dock a');
    dockLinks.forEach(link => {
      const href = link.getAttribute('href');
      const hrefNorm = href === '' ? 'index.html' : href;
      if (hrefNorm === norm) {
        link.className = 'text-stone-950 font-bold hover:text-brand transition-colors dock-active';
      } else {
        link.className = 'hover:text-stone-950 transition-colors text-stone-600';
      }
    });

    // Update mobile drawer links with active state
    const mobileLinks = document.querySelectorAll('#mobile-nav-menu a.mobile-nav-item, #mobile-nav-menu a.mobile-nav-link, #mobile-nav-menu a');
    mobileLinks.forEach(link => {
      const href = link.getAttribute('href');
      const hrefNorm = href === '' ? 'index.html' : href;
      if (hrefNorm === norm) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  },

  runPageScripts: function(targetUrl, rawHtml) {
    // Re-initialize 3D magnetic tilt
    const tiltCards = document.querySelectorAll('.specimen-card-3d');
    tiltCards.forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -7;
        const rotateY = ((x - centerX) / centerX) * 7;
        card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0px)';
      });
    });

    // Re-initialize Directional Scroll Engine
    const scrollCards = document.querySelectorAll('.card-scroll-item');
    if (scrollCards.length) {
      let lastScrollY = window.pageYOffset || document.documentElement.scrollTop;
      let scrollDirection = 'down';

      const onScroll = () => {
        const currentY = window.pageYOffset || document.documentElement.scrollTop;
        scrollDirection = currentY >= lastScrollY ? 'down' : 'up';
        lastScrollY = currentY <= 0 ? 0 : currentY;
      };
      window.addEventListener('scroll', onScroll, { passive: true });

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          const el = entry.target;
          if (entry.isIntersecting) {
            el.classList.remove('scroll-entering-down', 'scroll-entering-up');
            el.classList.add(scrollDirection === 'down' ? 'scroll-entering-down' : 'scroll-entering-up');
            void el.offsetWidth;
            el.classList.add('scroll-revealed');
          } else {
            const rect = el.getBoundingClientRect();
            if (rect.top > window.innerHeight || rect.bottom < 0) {
              el.classList.remove('scroll-revealed', 'scroll-entering-down', 'scroll-entering-up');
            }
          }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

      scrollCards.forEach(card => observer.observe(card));
    }

    // Re-execute scripts embedded in the page
    if (rawHtml) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(rawHtml, 'text/html');
      const scripts = doc.querySelectorAll('script');
      scripts.forEach(s => {
        if (s.src) return; // Skip external script re-loading
        const code = s.textContent.trim();
        if (!code || code.includes('CV_NAV.init')) return;
        try {
          const runner = new Function(code);
          runner();
        } catch(e) {}
      });
    }

    // Video playback for index.html
    if (targetUrl.includes('index') || targetUrl === '' || targetUrl === 'index.html') {
      const heroVideo = document.getElementById('hero-trade-video');
      if (heroVideo) {
        heroVideo.play().catch(() => {});
      }
    }
  }
};

// Global Video Controls (Unmute Sound & Playback)
window.toggleBgVideoBrightness = function() {
  const video = document.getElementById('bg-trade-video');
  const scrim = document.getElementById('bg-video-scrim');
  const btn = document.getElementById('bg-video-bright-btn');
  if (!video) return;

  const isBoosted = video.getAttribute('data-boosted') === 'true';
  if (isBoosted) {
    video.style.filter = 'brightness(1.0) contrast(1.05)';
    video.setAttribute('data-boosted', 'false');
    if (scrim) scrim.style.opacity = '0.55';
    if (btn) btn.innerHTML = '<span>☀️ Natural Visibility (100%)</span>';
  } else {
    video.style.filter = 'brightness(1.22) contrast(1.1)';
    video.setAttribute('data-boosted', 'true');
    if (scrim) scrim.style.opacity = '0.25';
    if (btn) btn.innerHTML = '<span>💡 High Visibility (120%)</span>';
  }
};

window.CV_TRADE = CV_TRADE;
window.toggleBgVideoMute = function() {
  if (window.CV_TRADE && typeof window.CV_TRADE.toggleBgVideoMute === 'function') {
    window.CV_TRADE.toggleBgVideoMute();
  }
};

window.toggleBgVideoPlay = function() {
  const video = document.getElementById('bg-trade-video') || document.querySelector('video');
  const btn = document.getElementById('bg-video-play-btn');
  if (!video) return;

  if (video.paused) {
    video.play().then(() => {
      if (btn) btn.innerHTML = '<span>⏸ Pause Video</span>';
    });
  } else {
    video.pause();
    if (btn) btn.innerHTML = '<span>▶ Play Video</span>';
  }
};

// Accordion Collapsible for Mobile Menu (Bulletproof Style & State)
window.toggleMobileAccordion = function(submenuId, btn) {
  const submenu = document.getElementById(submenuId);
  if (!submenu) return;
  const isHidden = submenu.classList.contains('hidden') || submenu.style.display === 'none';
  const icon = btn ? btn.querySelector('svg') : null;

  if (isHidden) {
    submenu.classList.remove('hidden');
    submenu.style.display = 'flex';
    submenu.classList.add('expanded');
    if (btn) {
      btn.classList.add('expanded');
      btn.classList.add('bg-stone-50', 'text-emerald-700');
    }
    if (icon) {
      icon.style.transform = 'rotate(180deg)';
      icon.style.color = '#059669';
    }
  } else {
    submenu.classList.add('hidden');
    submenu.style.display = 'none';
    submenu.classList.remove('expanded');
    if (btn) {
      btn.classList.remove('expanded');
      btn.classList.remove('bg-stone-50', 'text-emerald-700');
    }
    if (icon) {
      icon.style.transform = 'rotate(0deg)';
      icon.style.color = '';
    }
  }
};

// Voices Between Frames Carousel Animation Controls
window.toggleVoicesMarquee = function() {
  const track = document.getElementById('voices-track');
  const btn = document.getElementById('voices-play-toggle-btn');
  if (!track) return;
  const isPaused = track.classList.contains('paused');
  if (isPaused) {
    track.classList.remove('paused');
    if (btn) btn.innerHTML = '<span>⏸ Pause Flow</span>';
  } else {
    track.classList.add('paused');
    if (btn) btn.innerHTML = '<span>▶ Resume Flow</span>';
  }
};

window.scrollVoicesTrack = function(direction) {
  const wrapper = document.querySelector('.voices-marquee-wrapper');
  if (!wrapper) return;
  const scrollAmount = 400 * direction;
  wrapper.scrollBy({ left: scrollAmount, behavior: 'smooth' });
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  CV_TRADE.renderDocketUI();
  CV_NAV.init();
});
