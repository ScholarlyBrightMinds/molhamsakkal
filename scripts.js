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
        scholar:      `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5.242 13.769L.5 9.5 12 1l11.5 8.5-4.742 4.269C17.548 11.249 14.978 9.5 12 9.5s-5.548 1.749-6.758 4.269zM12 10a7 7 0 1 0 0 14 7 7 0 0 0 0-14z"/></svg>`,
        orcid:        `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.372 0 0 5.372 0 12s5.372 12 12 12 12-5.372 12-12S18.628 0 12 0zM7.369 17.353H5.844V7.08h1.525v10.273zM6.605 6.15a.925.925 0 1 1 0-1.85.925.925 0 0 1 0 1.85zm12.191 6.235c0 2.93-2.032 4.968-4.93 4.968h-3.87V7.08h3.87c2.898 0 4.93 2.068 4.93 5.305zm-1.56 0c0-2.037-1.214-3.913-3.37-3.913H11.52v7.827h2.346c2.156 0 3.37-1.876 3.37-3.914z"/></svg>`,
        github:       `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>`,
        instagram:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>`,
        email:        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>`,
        linkedin:     `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14zM8.339 18.338V10.67H5.667v7.668h2.672zM7.004 9.5a1.547 1.547 0 1 0 0-3.094 1.547 1.547 0 0 0 0 3.094zm11.335 8.838v-4.363c0-2.294-1.226-3.36-2.86-3.36a2.472 2.472 0 0 0-2.237 1.23v-1.057h-2.68c.035.76 0 7.668 0 7.668h2.68v-4.284c0-.24.018-.483.089-.655.195-.48.636-.977 1.378-.977.972 0 1.361.741 1.361 1.828v4.087h2.669z"/></svg>`,
        researchgate: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.5"/><path d="M9.2 7.5v9M9.2 7.5h3.7a2.6 2.6 0 0 1 0 5.2H9.2M12.6 12.7l3.2 3.8"/></svg>`,
        cv:           `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 18 15 15"/></svg>`,

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
        { key: 'research',     href: 'research.html',     label: 'Research' },
        { key: 'projects',     href: 'projects.html',     label: 'Projects' },
        { key: 'publications', href: 'publications.html', label: 'Publications' },
        { key: 'talks',        href: 'talks.html',        label: 'Talks' },
        { key: 'blog',         href: 'blog.html',         label: 'Blog' },
        { key: 'contact',      href: 'contact.html',      label: 'Contact' }
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

        // PhD CTA block — only renders if SITE_CONFIG.phdCTA exists
        if (C.phdCTA) {
            const cta = C.phdCTA;
            const html = `
                <div class="phd-cta-inner">
                    <span class="phd-cta-ribbon">${cta.ribbon}</span>
                    <h3 class="phd-cta-title">${cta.title}</h3>
                    <p class="phd-cta-body">${cta.body}</p>
                    <div class="phd-cta-actions">
                        <a class="phd-cta-btn phd-cta-btn--primary" href="${cta.primaryHref}">
                            ${ICONS.email}<span>${cta.primaryLabel}</span>
                        </a>
                        <a class="phd-cta-btn phd-cta-btn--secondary" href="${cta.secondaryHref}">
                            <span>${cta.secondaryLabel}</span>
                            <span class="phd-cta-arrow" aria-hidden="true">→</span>
                        </a>
                        <a class="phd-cta-btn phd-cta-btn--tertiary" href="${cta.tertiaryHref}" download>
                            ${ICONS.cv}<span>${cta.tertiaryLabel}</span>
                        </a>
                    </div>
                </div>
            `;
            setBind('phdCTA', html);
        }

        // Impact stats — big "By the numbers" tiles
        if (Array.isArray(C.impactStats) && C.impactStats.length) {
            const html = C.impactStats.map(s => `
                <div class="impact-tile${s.variant ? ' impact-tile--' + s.variant : ''}">
                    <div class="impact-num">${s.num}</div>
                    <div class="impact-label">${s.label}</div>
                    <div class="impact-sub">${s.sub || ''}</div>
                </div>
            `).join('');
            setBind('impactStats', html);
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
            blogLede:     C.ledes.blog,
            talksLede:    C.ledes.talks,
            contactLede:  C.ledes.contact,
            researchLede: C.ledes.research
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

        // Email for "Want to collaborate?" button
        const email = C.identity.email
                   || (C.ids && C.ids.email)
                   || (C.social && C.social.find(s => s.key === 'email')?.url?.replace('mailto:',''))
                   || '';

        el.innerHTML = C.projects.map((p, i) => {
            const kind = (p.statusKind || 'active').toLowerCase();
            const statusBadge = p.status
                ? `<span class="proj-status proj-status--${kind}">${p.status}</span>`
                : '';
            const needsLine = p.needs
                ? `<p class="proj-needs"><span class="proj-needs-label">Needs:</span> ${p.needs}</p>`
                : '';
            // Only show collaborate button on active / review projects (not already-published ones)
            const showCollab = kind === 'active' || kind === 'review' || kind === 'draft';
            const subject = encodeURIComponent(`Collaboration on "${p.title}"`);
            const body    = encodeURIComponent(`Hi ${C.identity.firstName || ''},\n\nI saw your "${p.title}" project on your website and would like to discuss a potential collaboration.\n\n`);
            const collabBtn = (showCollab && email)
                ? `<a class="proj-collab" href="mailto:${email}?subject=${subject}&body=${body}">
                     <span class="proj-collab-icon">✉</span>
                     Want to collaborate?
                   </a>`
                : '';
            // Published projects get a "Read paper" button pointing to the DOI
            const paperUrl  = p.doi ? `https://doi.org/${p.doi}` : (p.paperUrl || '');
            const venueLine = p.doi && p.venue
                ? `<span class="proj-venue">${p.venue}</span>`
                : '';
            const paperBtn  = paperUrl
                ? `<a class="proj-paper" href="${paperUrl}" target="_blank" rel="noopener">
                     <span class="proj-paper-icon" aria-hidden="true">↗</span>
                     <span>Read paper</span>
                     ${p.doi ? `<span class="proj-paper-doi">${p.doi}</span>` : ''}
                   </a>`
                : '';
            const actionsRow = (paperBtn || collabBtn)
                ? `<div class="proj-actions">${paperBtn}${collabBtn}</div>`
                : '';

            return `
            <article class="proj-card proj-card--${kind} reveal reveal-d${(i % 3) + 1}">
                <div class="proj-num">${p.n}</div>
                <div class="proj-body">
                    <div class="proj-meta">
                        <span class="proj-label">${p.label}</span>
                        ${statusBadge}
                        ${venueLine}
                    </div>
                    <h3 class="proj-title">${p.title}</h3>
                    <p class="proj-desc">${p.desc}</p>
                    ${needsLine}
                    ${p.tech ? `<div class="proj-tags">${p.tech.map(t => `<span class="proj-tag">${t}</span>`).join('')}</div>` : ''}
                    ${actionsRow}
                </div>
            </article>
            `;
        }).join('');

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
        el.innerHTML = C.blog.map((post, i) => {
            const coverKey = post.cover || 'default';
            const cover = `
                <div class="blog-cover blog-cover--${coverKey}" aria-hidden="true">
                    <span class="blog-cover-num">${String(i + 1).padStart(2, '0')}</span>
                    ${post.tag ? `<span class="blog-cover-tag">${post.tag}</span>` : ''}
                </div>
            `;
            const excerpt = post.excerpt
                ? `<p class="blog-excerpt">${post.excerpt}</p>`
                : '';
            const readingTime = post.readingTime
                ? `<span class="blog-readtime">${post.readingTime}</span>`
                : '';
            return `
                <a href="${post.file}" class="blog-item reveal reveal-d${(i % 3) + 1}">
                    ${cover}
                    <div class="blog-body">
                        <h3 class="blog-title">${post.title}</h3>
                        ${excerpt}
                        <div class="blog-meta">
                            <span class="blog-date">${post.date}</span>
                            ${readingTime}
                            <span class="blog-read">Read <span class="arrow">→</span></span>
                        </div>
                    </div>
                </a>
            `;
        }).join('');

        if (window.__revealObserver) {
            el.querySelectorAll('.reveal').forEach(r => window.__revealObserver.observe(r));
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  TALKS page bindings (talks.html)
    // ═══════════════════════════════════════════════════════════════
    function bindTalks() {
        const el = document.querySelector('[data-bind="talkList"]');
        if (!el || !Array.isArray(C.talks)) return;
        const kindLabel = {
            hackathon: 'Hackathon',
            poster:    'Poster',
            talk:      'Talk',
            workshop:  'Workshop',
            thesis:    'Thesis'
        };
        el.innerHTML = C.talks.map((t, i) => {
            const k = (t.kind || 'talk').toLowerCase();
            const awardBadge = t.award
                ? `<span class="talk-award">${t.award}</span>`
                : '';
            return `
                <article class="talk-card talk-card--${k} reveal reveal-d${(i % 3) + 1}">
                    <div class="talk-date">
                        <span class="talk-date-month">${t.date}</span>
                        <span class="talk-date-kind">${kindLabel[k] || 'Talk'}</span>
                    </div>
                    <div class="talk-body">
                        <div class="talk-meta-row">
                            ${awardBadge}
                        </div>
                        <h3 class="talk-title">${t.title}</h3>
                        <p class="talk-venue">${t.venue || ''}</p>
                        <p class="talk-desc">${t.desc || ''}</p>
                    </div>
                </article>
            `;
        }).join('');
        if (window.__revealObserver) {
            el.querySelectorAll('.reveal').forEach(r => window.__revealObserver.observe(r));
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  CONTACT page bindings (contact.html)
    // ═══════════════════════════════════════════════════════════════
    function bindContact() {
        if (!C.contact) return;

        const introEl = document.querySelector('[data-bind="contactIntro"]');
        if (introEl) {
            introEl.innerHTML = `
                <p class="contact-intro">${C.contact.intro}</p>
            `;
        }

        // Heading split (Let's + talk)
        const hEl = document.querySelector('[data-bind="contactH1"]');
        if (hEl) {
            hEl.innerHTML = `${C.contact.h1Front} <em>${C.contact.h1Accent}</em>.`;
        }

        const kEl = document.querySelector('[data-bind="contactKicker"]');
        if (kEl) kEl.textContent = C.contact.kicker;

        // Direct-contact card
        const dEl = document.querySelector('[data-bind="contactDirect"]');
        if (dEl) {
            const rows = [];
            rows.push(`
                <p class="contact-direct-row">
                    <span class="contact-direct-icon">${ICONS.email}</span>
                    <a class="contact-direct-link" href="mailto:${C.contact.directEmail}">${C.contact.directEmail}</a>
                </p>
            `);
            if (C.contact.cvHref) {
                const isPdf = /\.pdf($|\?)/i.test(C.contact.cvHref);
                const downloadAttr = isPdf ? ' download' : '';
                const label = isPdf ? 'Download CV (PDF)' : 'Request CV';
                rows.push(`
                <p class="contact-direct-row">
                    <span class="contact-direct-icon">${ICONS.cv}</span>
                    <a class="contact-direct-link" href="${C.contact.cvHref}"${downloadAttr}>${label}</a>
                </p>
                `);
            }
            if (C.ids && C.ids.linkedin) {
                rows.push(`
                <p class="contact-direct-row">
                    <span class="contact-direct-icon">${ICONS.linkedin}</span>
                    <a class="contact-direct-link" href="https://www.linkedin.com/in/${C.ids.linkedin}" target="_blank" rel="noopener">linkedin.com/in/${C.ids.linkedin}</a>
                </p>
                `);
            }
            rows.push(`<p class="contact-response-time">${C.contact.responseTimeNote || ''}</p>`);
            dEl.innerHTML = rows.join('');
        }

        // "For supervisors / collaborators / press" blocks
        const bEl = document.querySelector('[data-bind="contactBlocks"]');
        if (bEl && Array.isArray(C.contact.blocks)) {
            bEl.innerHTML = C.contact.blocks.map((b, i) => `
                <article class="contact-block reveal reveal-d${(i % 3) + 1}">
                    <div class="contact-block-icon" aria-hidden="true">${b.icon || '·'}</div>
                    <h3 class="contact-block-title">${b.title}</h3>
                    <p class="contact-block-body">${b.body}</p>
                </article>
            `).join('');
            if (window.__revealObserver) {
                bEl.querySelectorAll('.reveal').forEach(r => window.__revealObserver.observe(r));
            }
        }

        // Wire the form action + show a note if endpoint not yet configured
        const form = document.querySelector('form.contact-form');
        if (form) {
            const action = C.contact.formAction || '';
            const noteEl = form.querySelector('[data-bind="contactFormNote"]');
            if (action && !action.includes('REPLACE_WITH_FORMSPREE_ID')) {
                form.setAttribute('action', action);
                if (noteEl) noteEl.style.display = 'none';
            } else {
                // Disable submission until a real endpoint is configured
                form.setAttribute('data-disabled', 'true');
                form.addEventListener('submit', e => e.preventDefault());
                if (noteEl) noteEl.textContent = C.contact.formNote || '';
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  RESEARCH STATEMENT page bindings (research.html)
    // ═══════════════════════════════════════════════════════════════
    function bindResearch() {
        if (!C.research) return;

        const kEl = document.querySelector('[data-bind="researchKicker"]');
        if (kEl) kEl.textContent = C.research.kicker;

        const hEl = document.querySelector('[data-bind="researchH1"]');
        if (hEl) {
            hEl.innerHTML = `${C.research.h1Front} <em>${C.research.h1Accent}</em>.`;
        }

        const iEl = document.querySelector('[data-bind="researchIntro"]');
        if (iEl) iEl.innerHTML = C.research.intro;

        const sEl = document.querySelector('[data-bind="researchSections"]');
        if (sEl && Array.isArray(C.research.sections)) {
            sEl.innerHTML = C.research.sections.map((s, i) => `
                <article class="research-block reveal reveal-d${(i % 3) + 1}">
                    <p class="sec-kicker">${s.kicker}</p>
                    <h2 class="research-block-title">${s.title}</h2>
                    <div class="research-block-body">
                        ${(s.body || []).map(p => `<p>${p}</p>`).join('')}
                    </div>
                </article>
            `).join('');
            if (window.__revealObserver) {
                sEl.querySelectorAll('.reveal').forEach(r => window.__revealObserver.observe(r));
            }
        }

        const fEl = document.querySelector('[data-bind="researchFinalCTA"]');
        if (fEl && C.research.finalCTAText) {
            fEl.innerHTML = `
                <a class="research-final-cta" href="${C.research.finalCTAHref}">
                    ${ICONS.email}<span>${C.research.finalCTAText}</span>
                </a>
            `;
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  ARC (scrollytelling research-arc page · arc.html)
    // ═══════════════════════════════════════════════════════════════
    function bindArc() {
        if (!C.arc) return;

        const kEl = document.querySelector('[data-bind="arcKicker"]');
        if (kEl) kEl.textContent = C.arc.kicker;

        const hEl = document.querySelector('[data-bind="arcH1"]');
        if (hEl) {
            hEl.innerHTML = `${C.arc.h1Front} <em>${C.arc.h1Accent}</em>.`;
        }

        const iEl = document.querySelector('[data-bind="arcIntro"]');
        if (iEl) iEl.textContent = C.arc.intro || '';

        const trackEl = document.querySelector('[data-bind="arcChapters"]');
        if (!trackEl || !Array.isArray(C.arc.chapters)) return;

        trackEl.innerHTML = C.arc.chapters.map(ch => {
            const bodyHtml = (ch.body || []).map(p => `<p class="arc-step-body">${p}</p>`).join('');
            let milestoneHtml = '';
            if (ch.milestone) {
                const tag = ch.milestone.href ? 'a' : 'div';
                const hrefAttr = ch.milestone.href
                    ? ` href="${ch.milestone.href}" target="_blank" rel="noopener noreferrer"` : '';
                milestoneHtml = `
                    <${tag} class="arc-milestone"${hrefAttr}>
                        <span class="arc-milestone-dot" aria-hidden="true"></span>
                        <span class="arc-milestone-text">
                            <span class="arc-milestone-label">${ch.milestone.label || ''}</span>
                            ${ch.milestone.sub ? `<span class="arc-milestone-sub">${ch.milestone.sub}</span>` : ''}
                        </span>
                    </${tag}>`;
            }
            return `
                <section class="arc-step" data-arc-key="${ch.key || ''}" data-arc-frame="${ch.frame || ch.key || ''}">
                    <p class="arc-step-kicker">${ch.kicker || ''}</p>
                    <h2 class="arc-step-title">${ch.title || ''}</h2>
                    ${bodyHtml}
                    ${milestoneHtml}
                </section>
            `;
        }).join('');
    }

    // ═══════════════════════════════════════════════════════════════
    //  PUBLICATION FILTERS (publications.html)
    // ═══════════════════════════════════════════════════════════════
    function wireFilters() {
        const bar = document.querySelector('.pub-filters');
        const list = document.getElementById('list-articles');
        if (!bar || !list) return;

        const buttons = Array.from(bar.querySelectorAll('.pub-filter'));
        const articles = Array.from(list.querySelectorAll('article.pub-item'));
        const counter = document.querySelector('.pub-filter-count');

        function applyFilter(filter) {
            const [kind, value] = filter.split(':');
            let shownCount = 0;
            articles.forEach(a => {
                const yr = a.getAttribute('data-year') || '';
                const topics = (a.getAttribute('data-topic') || '').split(/\s+/);
                let show = false;
                if (kind === 'all') show = true;
                else if (kind === 'year')  show = yr === value;
                else if (kind === 'topic') show = topics.includes(value);
                a.classList.toggle('pub-hidden', !show);
                if (show) shownCount += 1;
            });
            if (counter) {
                counter.textContent = shownCount === articles.length
                    ? `${shownCount} papers`
                    : `${shownCount} of ${articles.length}`;
            }
        }

        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                applyFilter(btn.getAttribute('data-filter') || 'all');
            });
        });

        // Initial state — show All
        const allBtn = bar.querySelector('.pub-filter[data-filter="all"]');
        if (allBtn) allBtn.classList.add('active');
        applyFilter('all');
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
        bindTalks();
        bindContact();
        bindResearch();
        bindArc();
        wireFilters();
        wireTheme();
        wireMobile();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
