// ═══════════════════════════════════════════════════════════════════
//  theme.config.js — Molham Sakkal
//  Single source of truth for this researcher's site.
// ═══════════════════════════════════════════════════════════════════

window.SITE_CONFIG = {

    // ── Identity ──────────────────────────────────────────────────
    identity: {
        fullName:  "Molham Sakkal",
        firstName: "Molham",
        lastName:  "Sakkal",
        initials:  "MS",
        role:      "Cancer Biology × Drug Delivery",
        tagline:   "Cancer cell biology &amp; nanomedicine — designing smarter ways to target and treat cancer while reducing off-target toxicity.",
        location:  "Abu Dhabi, UAE",
        status:    "leading molecular oncology projects at HBRC",
        photo:     "images/profile.png",
        affiliation: {
            name: "Health and Biomedical Research Center",
            url:  "https://www.aau.ac.ae/",
            role: "Laboratory &amp; Research Supervisor"
        }
    },

    // ── Palette ── indigo (hub-assigned for Molham) ──────────────
    palette: {
        name: "indigo",
        dark: {
            bg:          "#0d0f1a",
            bgSoft:      "#141729",
            bgDeep:      "#080a14",
            card:        "#1a1d36",
            cardSoft:    "#15182d",
            text:        "#ebe8f5",
            textSoft:    "#b5b0cc",
            muted:       "#6e6890",
            border:      "#272a4c",
            borderS:     "#1f2240",
            accent:      "#8b88e8",    /* indigo — soft luminous */
            accentD:     "#a5a3ee",
            accentBg:    "rgba(139,136,232,0.10)",
            accentGlow:  "rgba(139,136,232,0.22)",
            amber:       "#e6b76c",
            amberBg:     "rgba(230,183,108,0.10)",
            amberGlow:   "rgba(230,183,108,0.18)"
        },
        light: {
            bg:          "#f6f4fb",
            bgSoft:      "#eeebf7",
            bgDeep:      "#e5e1f2",
            card:        "#ffffff",
            cardSoft:    "#faf8ff",
            text:        "#1a1733",
            textSoft:    "#3d3a5c",
            muted:       "#7a7599",
            border:      "#ddd7ec",
            borderS:     "#ebe6f5",
            accent:      "#4338ca",    /* indigo — deep */
            accentD:     "#3827a8",
            accentBg:    "#ebe7fa",
            accentGlow:  "rgba(67,56,202,0.14)",
            amber:       "#8a5a1e",
            amberBg:     "#f4ead6",
            amberGlow:   "rgba(138,90,30,0.14)"
        }
    },

    // ── IDs (external profiles) ───────────────────────────────────
    ids: {
        scholar: "JO1OQj8AAAAJ",
        scopus:  "58209400600",
        orcid:   "0000-0001-6081-1284",
        github:  "ScholarlyBrightMinds",
        email:   "Molham.sakkal@gmail.com"
    },

    // ── Social links ──────────────────────────────────────────────
    social: [
        { key: "scholar", label: "Google Scholar", url: "https://scholar.google.com/citations?user=JO1OQj8AAAAJ&hl=en" },
        { key: "scopus",  label: "Scopus",         url: "https://www.scopus.com/authid/detail.uri?authorId=58209400600" },
        { key: "orcid",   label: "ORCID",          url: "https://orcid.org/0000-0001-6081-1284" },
        { key: "github",  label: "GitHub",         url: "https://github.com/ScholarlyBrightMinds" },
        { key: "email",   label: "Email",          url: "mailto:Molham.sakkal@gmail.com" }
    ],

    // ── Bio ──────────────────────────────────────────────────────
    bio: {
        short: "Cancer Cell Biology &amp; Drug Delivery researcher at the Health and Biomedical Research Center, Al Ain University. I spend long hours with analytical instruments and cancer cell lines — and somehow find it exciting.",
        long:  "I hold a Bachelor's in Pharmacy and a Master's in Pharmaceutical Sciences from Al Ain University, where I specialized in drug delivery and formulation development. During my master's I worked as a Research and Laboratory Assistant, and that's when I really caught the research bug."
    },

    // ── Hero chips ────────────────────────────────────────────────
    chips: [
        { label: "8 Publications · 23 Citations" },
        { label: "h-index 3" },
        { label: "Lab &amp; Research Supervisor" },
        { label: "MSc Pharm. Sci. · Al Ain University" },
        { label: "🔬 Cancer Cell Biology", variant: "gold" }
    ],

    // ── Per-page sub-hero lede text ──────────────────────────────
    ledes: {
        about:        "Cancer cell biology &amp; drug delivery researcher, leading molecular oncology projects and collaborating across UAEU, NYU Abu Dhabi, and the University of Sharjah.",
        projects:     "Active work across cancer cell biology, nanomedicine, and bioinformatics. Some are published, some ongoing in the lab.",
        publications: "Peer-reviewed output across cancer biology, drug delivery, and nanomedicine — updated automatically from Scholar and Scopus.",
        blog:         "Lab notes, research reflections, and the occasional write-up from conferences and collaborations."
    },

    // ── About page ────────────────────────────────────────────────
    about: {
        paragraphs: [
            "I hold a <strong>Bachelor's in Pharmacy</strong> and a <strong>Master's in Pharmaceutical Sciences</strong> from Al Ain University, where I specialized in drug delivery and formulation development. During my master's, I worked as a Research and Laboratory Assistant — and that's when I really caught the research bug. Spending long hours with analytical instruments and cancer cell lines turned out to be more exciting than I expected.",
            "I'm now a <strong>Laboratory and Research Supervisor</strong> at the <strong>Health and Biomedical Research Center (HBRC)</strong>, where I lead research projects in molecular oncology, cancer cell biology, and drug delivery systems. I also train and guide postgraduate students in advanced cell culture techniques and experimental design.",
            "My collaborations span institutions like <strong>UAEU</strong>, <strong>NYU Abu Dhabi</strong>, and the <strong>University of Sharjah</strong>. I'm passionate about <em>bridging laboratory innovation with real-world therapeutic impact</em> as I pursue my PhD studies."
        ],

        timeline: [
            { date: "BSc · Al Ain University",         title: "Bachelor of Pharmacy (B.Pharm.)",     desc: "Foundational training in pharmaceutical sciences." },
            { date: "MSc · Al Ain University",         title: "Pharmaceutical Sciences",             desc: "Specialization in drug delivery &amp; formulation." },
            { date: "Research Assistant",              title: "Caught the research bug",             desc: "Long hours with analytical instruments &amp; cancer cell lines." },
            { date: "Current · HBRC",                  title: "Lab &amp; Research Supervisor",       desc: "Leading molecular oncology &amp; drug delivery projects; training postgrads.", state: "current" },
            { date: "Current · Collaborations",        title: "UAEU · NYU Abu Dhabi · U. Sharjah",   desc: "Multi-institution collaborations in cancer biology &amp; nanomedicine.", state: "current" },
            { date: "Next · PhD",                      title: "Translational cancer research",       desc: "PhD in precision nanomedicine &amp; targeted drug delivery.", state: "future" }
        ],

        pillars: [
            { icon: "flask",    title: "Cancer Cell Biology",    desc: "Cell culture, cytotoxic screening, gene knockout studies, molecular oncology pathway analysis." },
            { icon: "molecule", title: "Drug Delivery &amp; Nanomedicine", desc: "Nanoformulations, targeted delivery systems, inhalable nanoparticle design for cancer therapy." },
            { icon: "chart",    title: "Bioinformatics",         desc: "Computational identification of therapeutic targets; cancer genomics; statistical analysis." }
        ],

        awards: [
            { icon: "🎓", title: "MSc in Pharmaceutical Sciences",  venue: "Al Ain University, UAE" },
            { icon: "🔬", title: "Laboratory &amp; Research Supervisor",  venue: "Health &amp; Biomedical Research Center" },
            { icon: "🤝", title: "Multi-institution collaborations",  venue: "UAEU · NYU Abu Dhabi · University of Sharjah" }
        ]
    },

    // ── Ongoing research ─────────────────────────────────────────
    // statusKind: 'active' | 'review' | 'published' | 'draft'
    projects: [
        {
            n: "01",
            label: "Cancer · Combination Therapy",
            title: "Synergistic Anticancer Drug Combinations",
            desc: "Enhancing treatment outcomes through drug–drug synergy. Evaluating combinations of cytotoxic agents across cancer cell lines to identify formulations that lower effective dose and reduce off-target toxicity.",
            tech: ["Cell Culture", "Cytotoxicity", "Combination Index", "IC50"],
            status: "Active — wet-lab screening",
            statusKind: "active",
            needs: "Looking for collaborators with access to additional cancer cell-line panels or combination-index analysis tooling."
        },
        {
            n: "02",
            label: "Molecular Oncology",
            title: "Gene Knockout Studies in Resistance Mechanisms",
            desc: "Unraveling molecular pathways and resistance mechanisms in cancer cells. Using gene knockout approaches to identify key drivers of chemoresistance and potential vulnerabilities.",
            tech: ["CRISPR", "Cell Biology", "Molecular Pathways", "Resistance"],
            status: "Active — ongoing knockout experiments",
            statusKind: "active",
            needs: "Open to collaborators in molecular oncology, CRISPR methodology, or resistance-pathway bioinformatics."
        },
        {
            n: "03",
            label: "Drug Discovery · Screening",
            title: "Novel Compound Cytotoxic Screening",
            desc: "Evaluating cytotoxic potential of novel compounds across a panel of cancer cell lines. Identifying lead structures for further development and mechanism-of-action studies.",
            tech: ["HTS", "Cell Viability", "Cancer Lines", "Lead Discovery"],
            status: "Active — screening campaigns",
            statusKind: "active",
            needs: "Medicinal chemists with novel compound libraries welcome — especially synthetic natural-product derivatives."
        },
        {
            n: "04",
            label: "Bioinformatics",
            title: "Computational Identification of Gene Targets",
            desc: "Bioinformatics pipelines for identifying novel therapeutic targets in cancer genomics. Bridging computational predictions with wet-lab validation.",
            tech: ["Bioinformatics", "Cancer Genomics", "Target ID", "Computational Biology"],
            status: "Active — pipeline development",
            statusKind: "active",
            needs: "Computational biologists or ML researchers interested in cancer-genomics target prediction, especially for wet-lab validation partnerships."
        },
        {
            n: "05",
            label: "Nanomedicine · Drug Delivery",
            title: "Engineered Nanoformulations",
            desc: "Engineering targeted delivery systems for improved therapeutic efficacy. Focus on inhalable nanoparticles for non-small cell lung cancer and smart chemotherapy platforms.",
            tech: ["Nanoparticles", "Drug Delivery", "Targeted Therapy", "NSCLC"],
            status: "Published · Saudi Pharmaceutical Journal · 2025",
            statusKind: "published"
        }
    ],

    // ── Blog ──────────────────────────────────────────────────────
    // Empty until Molham writes some posts. Blog page will show an empty state.
    blog: [],

    // ── Footer ────────────────────────────────────────────────────
    footer: {
        copyrightYear: 2026,
        tagline: "Part of the Scholarly Bright Minds hub.",
        credits: "A fork of <a href=\"https://github.com/muhammedrashidx/ScholarSite_2.0\" target=\"_blank\" rel=\"noopener\">ScholarSite_2.0</a>."
    }
};

// ═══════════════════════════════════════════════════════════════════
//  APPLY PALETTE TO CSS VARIABLES — same logic as Abdallah's
// ═══════════════════════════════════════════════════════════════════
(function applyPalette() {
    const P = window.SITE_CONFIG.palette;
    const root = document.documentElement;

    function setMode(mode) {
        const p = P[mode];
        Object.entries(p).forEach(([k, v]) => {
            const cssVar = '--' + k.replace(/([A-Z])/g, '-$1').toLowerCase();
            root.style.setProperty(cssVar, v);
        });
    }

    let theme = null;
    try { theme = localStorage.getItem('sbm-theme'); } catch (e) {}
    if (!theme) theme = 'dark';

    root.setAttribute('data-theme', theme);
    setMode(theme);

    window.__applyTheme = function(mode) {
        root.setAttribute('data-theme', mode);
        setMode(mode);
        try { localStorage.setItem('sbm-theme', mode); } catch (e) {}
        const hL = document.getElementById('hljs-light');
        const hD = document.getElementById('hljs-dark');
        if (hL && hD) { hL.disabled = (mode === 'dark'); hD.disabled = (mode !== 'dark'); }
    };
})();
