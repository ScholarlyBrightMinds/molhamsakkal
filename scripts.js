// ═══════════════════════════════════════════════════════════════════
//  scripts.js · Shared runtime for all pages
//
//  Responsibilities:
//    1. Render the nav bar + footer from SITE_CONFIG (consistent everywhere)
//    2. Data-bind hero fields on the home page (data-bind attributes)
//    3. Theme toggle (delegates to window.__applyTheme from theme.config.js)
//    4. Scroll-reveal observer
//    5. Mobile hamburger behaviour
//
//  IMPORTANT: This file must be tolerant of pages that don't have all the
//  binding targets — skip silently if an element isn't present.
// ═══════════════════════════════════════════════════════════════════

(function () {
    'use strict';

    const C = window.SITE_CONFIG;
    if (!C) {
        console.error('SITE_CONFIG missing — theme.config.js must load before scripts.js');
        return;
    }

    // ── SVG icons used across the site (kept inline to avoid image requests)
    const ICONS = {
        sun: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>`,
        moon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,

        // Social platform icons
        scholar:   `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5.242 13.769L.5 9.5 12 1l11.5 8.5-4.742 4.269C17.548 11.249 14.978 9.5 12 9.5s-5.548 1.749-6.758 4.269zM12 10a7 7 0 1 0 0 14 7 7 0 0 0 0-14z"/></svg>`,
        scopus:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M17 8c-1-2-3-3-5-3-3 0-5 2-5 4s2 3 5 4 5 2 5 4-2 4-5 4c-2 0-4-1-5-3"/></svg>`,
        orcid:     `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.372 0 0 5.372 0 12s5.372 12 12 12 12-5.372 12-12S18.628 0 12 0zM7.369 17.353H5.844V7.08h1.525v10.273zM6.605 6.15a.925.925 0 1 1 0-1.85.925.925 0 0 1 0 1.85zm12.191 6.235c0 2.93-2.032 4.968-4.93 4.968h-3.87V7.08h3.87c2.898 0 4.93 2.068 4.93 5.305zm-1.56 0c0-2.037-1.214-3.913-3.37-3.913H11.52v7.827h2.346c2.156 0 3.37-1.876 3.37-3.914z"/></svg>`,
        github:    `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>`,
        instagram: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>`,
        email:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>`,
        linkedin:  `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14zM8.339 18.338V10.67H5.667v7.668h2.672zM7.004 9.5a1.547 1.547 0 1 0 0-3.094 1.547 1.547 0 0 0 0 3.094zm11.335 8.838v-4.363c0-2.294-1.226-3.36-2.86-3.36a2.472 2.472 0 0 0-2.237 1.23v-1.057h-2.68c.035.76 0 7.668 0 7.668h2.68v-4.284c0-.24.018-.483.089-.655.195-.48.636-.977 1.378-.977.972 0 1.361.741 1.361 1.828v4.087h2.669z"/></svg>`,

        // Research pillar icons
        molecule: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="12,3 21,8 21,16 12,21 3,16 3,8"/><line x1="12" y1="3" x2="12" y2="21"/><line x1="3" y1="8" x2="21" y2="16"/><line x1="21" y1="8" x2="3" y2="16"/></svg>`,
        network:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><circle cx="12" cy="12" r="2.5"/><line x1="6.8" y1="7.2" x2="10.2" y2="10.6"/><line x1="17.2" y1="7.2" x2="13.8" y2="10.6"/><line x1="6.8" y1="16.8" x2="10.2" y2="13.4"/><line x1="17.2" y1="16.8" x2="13.8" y2="13.4"/></svg>`,
        document: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="14" rx="2"/><line x1="4" y1="9" x2="20" y2="9"/><circle cx="7.5" cy="13" r="0.5" fill="currentColor"/><line x1="10" y1="13" x2="17" y2="13"/><circle cx="7.5" cy="16" r="0.5" fill="currentColor"/><line x1="10" y1="16" x2="14" y2="16"/></svg>`,
        flask:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><line x1="7" y1="15" x2="17" y2="15"/></svg>`,
        chart:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="20" x2="20" y2="20"/><path d="M6 16l4-6 3 4 5-8"/></svg>`
    };

    // ═══════════════════════════════════════════════════════════════
    //  NAV rendering
    // ═══════════════════════════════════════════════════════════════

    const PAGES = [
        { key: 'home',         href: 'index.html',        label: 'Home' },
        { key: 'about',        href: 'about.html',        label: 'About' },
        { key: 'projects',     href: 'projects.html',     label: 'Ongoing Research' },
        { key: 'publications', href: 'publications.html', label: 'Publications' },
        { key: 'blog',         href: 'blog.html',         label: 'Blog' }
    ];

    function renderNav() {
        const nav = document.querySelector('.nav');
        if (!nav) return;
        const active = nav.getAttribute('data-page') || '';

        const menuItems = PAGES.map(p =>
            `<a href="${p.href}" class="nav-item ${p.key === active ? 'active' : ''}">${p.label}</a>`
        ).join('');

        nav.innerHTML = `
            <a href="index.html" class="brand">
                <span class="brand-dot"></span>
                ${C.identity.fullName}
                <span class="brand-meta">${C.identity.role}</span>
            </a>
            <div class="nav-right">
                <div class="hamburger" aria-label="Menu"><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>
                <div class="nav-menu">${menuItems}</div>
                <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme" title="Toggle day/night">
                    <span class="icon-sun">${ICONS.sun}</span>
                    <span class="icon-moon">${ICONS.moon}</span>
                </button>
            </div>
        `;
    }

    // ═══════════════════════════════════════════════════════════════
    //  FOOTER rendering
    // ═══════════════════════════════════════════════════════════════
    function renderFooter() {
        const f = document.querySelector('footer[data-bind="footer"]');
        if (!f) return;
        const links = (C.social || []).map(s => `<a href="${s.url}" target="_blank" rel="noopener">${s.label}</a>`).join('');
        f.innerHTML = `
            <div class="footer-left">
                <div>${C.identity.fullName} · ${C.identity.location} · © ${C.footer.copyrightYear}</div>
                <div class="colophon">
                    ${C.footer.tagline} Fraunces · Manrope · JetBrains Mono. ${C.footer.credits}
                </div>
            </div>
            <div class="footer-links">${links}</div>
        `;
    }

    // ═══════════════════════════════════════════════════════════════
    //  HERO / HOME bindings
    // ═══════════════════════════════════════════════════════════════
    function bindHome() {
        function setBind(key, html) {
            const el = document.querySelector(`[data-bind="${key}"]`);
            if (el) el.innerHTML = html;
        }

        // Text bindings
        setBind('statusText', `Currently · ${C.identity.status}`);

        // Split name for italic emphasis on last word
        const parts = C.identity.fullName.split(' ');
        const last = parts.pop();
        setBind('heading', `${parts.join(' ')}<br><em>${last}</em>`);

        setBind('tagline', C.identity.tagline);
        setBind('bio', C.bio.short);

        // Chips
        const chipsHTML = (C.chips || []).map(c =>
            `<span class="chip${c.variant ? ' ' + c.variant : ''}"><span class="dot"></span>${c.label}</span>`
        ).join('');
        setBind('chips', chipsHTML);

        // Social icons
        const socialHTML = (C.social || []).map(s => {
            const icon = ICONS[s.key] || ICONS.github;
            return `<a href="${s.url}" class="social-icon" target="_blank" rel="noopener" aria-label="${s.label}" title="${s.label}">${icon}</a>`;
        }).join('');
        setBind('social', socialHTML);

        // Profile photo
        const photoEl = document.querySelector('[data-bind="photo"]');
        if (photoEl) photoEl.src = C.identity.photo;

        // Research pillars on home
        const pillars = C.about && C.about.pillars;
        if (pillars) {
            const html = pillars.map(p => `
                <div class="hp-card">
                    <div class="hp-icon">${ICONS[p.icon] || ICONS.molecule}</div>
                    <h3 class="hp-title">${p.title}</h3>
                    <p class="hp-desc">${p.desc}</p>
                </div>
            `).join('');
            setBind('pillars', html);
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  SUB-HERO lede text (runs on every sub-page)
    // ═══════════════════════════════════════════════════════════════
    function bindLedes() {
        if (!C.ledes) return;
        const map = {
            aboutLede:    C.ledes.about,
            projectsLede: C.ledes.projects,
            pubsLede:     C.ledes.publications,
            blogLede:     C.ledes.blog
        };
        for (const [key, text] of Object.entries(map)) {
            const el = document.querySelector(`[data-bind="${key}"]`);
            if (el && text) el.innerHTML = text;
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  ABOUT page bindings
    // ═══════════════════════════════════════════════════════════════
    function bindAbout() {
        if (!C.about) return;

        const paraEl = document.querySelector('[data-bind="aboutParagraphs"]');
        if (paraEl && C.about.paragraphs) {
            paraEl.innerHTML = C.about.paragraphs.map(p => `<p>${p}</p>`).join('');
        }

        const tlEl = document.querySelector('[data-bind="timeline"]');
        if (tlEl && C.about.timeline) {
            tlEl.innerHTML = C.about.timeline.map(item => {
                const cls = item.state ? ` ${item.state}` : '';
                return `
                    <div class="tl-item${cls}">
                        <p class="tl-date">${item.date}</p>
                        <p class="tl-title">${item.title}</p>
                        <p class="tl-desc">${item.desc}</p>
                    </div>
                `;
            }).join('');
        }

        const pEl = document.querySelector('[data-bind="aboutPillars"]');
        if (pEl && C.about.pillars) {
            pEl.innerHTML = C.about.pillars.map(p => `
                <div class="pillar-card">
                    <div class="p-icon">${ICONS[p.icon] || ICONS.molecule}</div>
                    <h3 class="p-title">${p.title}</h3>
                    <p class="p-desc">${p.desc}</p>
                </div>
            `).join('');
        }

        const awEl = document.querySelector('[data-bind="awards"]');
        if (awEl && C.about.awards) {
            awEl.innerHTML = C.about.awards.map(a => `
                <li class="award-item">
                    <div class="award-icon">${a.icon}</div>
                    <div class="award-body">
                        <p class="a-title">${a.title}</p>
                        <p class="a-venue">${a.venue}</p>
                    </div>
                </li>
            `).join('');
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  PROJECTS page bindings
    // ═══════════════════════════════════════════════════════════════
    function bindProjects() {
        const el = document.querySelector('[data-bind="projectList"]');
        if (!el || !C.projects) return;
        el.innerHTML = C.projects.map((p, i) => `
            <article class="proj-card reveal reveal-d${(i % 3) + 1}">
                <div class="proj-num">${p.n}</div>
                <div class="proj-body">
                    <div class="proj-meta">
                        <span class="proj-label">${p.label}</span>
                        ${p.status ? `<span class="proj-status">${p.status}</span>` : ''}
                    </div>
                    <h3 class="proj-title">${p.title}</h3>
                    <p class="proj-desc">${p.desc}</p>
                    ${p.tech ? `<div class="proj-tags">${p.tech.map(t => `<span class="proj-tag">${t}</span>`).join('')}</div>` : ''}
                </div>
            </article>
        `).join('');

        if (window.__revealObserver) {
            el.querySelectorAll('.reveal').forEach(r => window.__revealObserver.observe(r));
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  BLOG page bindings
    // ═══════════════════════════════════════════════════════════════
    function bindBlog() {
        const el = document.querySelector('[data-bind="blogList"]');
        if (!el) return;
        if (!C.blog || C.blog.length === 0) {
            el.innerHTML = `
                <div class="blog-empty">
                    <p class="blog-empty-icon">📝</p>
                    <h3 class="blog-empty-title">Nothing here yet.</h3>
                    <p class="blog-empty-desc">Writing takes time. Check back soon — or follow my research on <a href="${C.social.find(s=>s.key==='scholar')?.url || '#'}" target="_blank" rel="noopener">Google Scholar</a>.</p>
                </div>
            `;
            return;
        }
        el.innerHTML = C.blog.map((post, i) => `
            <a href="${post.file}" class="blog-item reveal reveal-d${(i % 3) + 1}">
                <div class="blog-item-head">
                    <span class="blog-num">${String(i + 1).padStart(2, '0')}</span>
                    ${post.tag ? `<span class="blog-tag">${post.tag}</span>` : ''}
                </div>
                <h3 class="blog-title">${post.title}</h3>
                <div class="blog-meta">
                    <span class="blog-date">${post.date}</span>
                    <span class="blog-read">Read <span class="arrow">→</span></span>
                </div>
            </a>
        `).join('');

        if (window.__revealObserver) {
            el.querySelectorAll('.reveal').forEach(r => window.__revealObserver.observe(r));
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  THEME TOGGLE wiring
    // ═══════════════════════════════════════════════════════════════
    function wireTheme() {
        const btn = document.getElementById('themeToggle');
        if (!btn) return;
        btn.addEventListener('click', () => {
            const cur = document.documentElement.getAttribute('data-theme') || 'dark';
            (window.__applyTheme || (() => {}))(cur === 'dark' ? 'light' : 'dark');
        });
    }

    // ═══════════════════════════════════════════════════════════════
    //  SCROLL REVEAL
    // ═══════════════════════════════════════════════════════════════
    function wireReveal() {
        if (!('IntersectionObserver' in window)) {
            document.querySelectorAll('.reveal').forEach(el => el.classList.add('vis'));
            return;
        }
        const observer = new IntersectionObserver(entries => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    e.target.classList.add('vis');
                    observer.unobserve(e.target);
                }
            });
        }, { threshold: 0.01, rootMargin: '0px 0px -5% 0px' });
        document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
        // Expose so dynamically-added elements can register
        window.__revealObserver = observer;
    }

    // ═══════════════════════════════════════════════════════════════
    //  MOBILE hamburger
    // ═══════════════════════════════════════════════════════════════
    function wireMobile() {
        const hamburger = document.querySelector('.hamburger');
        const navMenu   = document.querySelector('.nav-menu');
        if (!hamburger || !navMenu) return;

        function toggle() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('show');
        }
        function close() {
            hamburger.classList.remove('active');
            navMenu.classList.remove('show');
        }

        hamburger.addEventListener('click', e => { e.stopPropagation(); toggle(); });
        document.addEventListener('click', e => {
            if (!navMenu.contains(e.target) && !hamburger.contains(e.target) && hamburger.classList.contains('active')) {
                close();
            }
        });
        window.addEventListener('resize', () => {
            if (window.innerWidth > 760) close();
        });
    }

    // ═══════════════════════════════════════════════════════════════
    //  INIT
    // ═══════════════════════════════════════════════════════════════
    function init() {
        renderNav();
        renderFooter();
        bindHome();
        bindLedes();
        wireReveal();
        bindAbout();
        bindProjects();
        bindBlog();
        wireTheme();
        wireMobile();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
