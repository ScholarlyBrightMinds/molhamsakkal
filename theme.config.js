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
        tagline:   "Cancer cell biology &amp; nanomedicine. Designing smarter ways to target and treat cancer while reducing off-target toxicity.",
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
        orcid:   "0000-0001-6081-1284",
        github:  "ScholarlyBrightMinds",
        email:   "Molham.sakkal@gmail.com"
    },

    // ── Social links ──────────────────────────────────────────────
    social: [
        { key: "scholar", label: "Google Scholar", url: "https://scholar.google.com/citations?user=JO1OQj8AAAAJ&hl=en" },
        { key: "orcid",   label: "ORCID",          url: "https://orcid.org/0000-0001-6081-1284" },
        { key: "github",  label: "GitHub",         url: "https://github.com/ScholarlyBrightMinds" },
        { key: "email",   label: "Email",          url: "mailto:Molham.sakkal@gmail.com" }
    ],

    // ── Bio ──────────────────────────────────────────────────────
    bio: {
        short: "Cancer Cell Biology &amp; Drug Delivery researcher at the Health and Biomedical Research Center, Al Ain University. I spend long hours with analytical instruments and cancer cell lines, and somehow find it exciting.",
        long:  "I hold a Bachelor's in Pharmacy and a Master's in Pharmaceutical Sciences from Al Ain University, where I specialized in drug delivery and formulation development. During my master's I worked as a Research and Laboratory Assistant, and that's when I really caught the research bug."
    },

    // ── Hero chips ────────────────────────────────────────────────
    chips: [
        { label: "15 Publications · 112 Citations" },
        { label: "h-index 6" },
        { label: "Lab &amp; Research Supervisor" },
        { label: "MSc Pharm. Sci. · Al Ain University" },
        { label: "🔬 Cancer Cell Biology", variant: "gold" }
    ],

    // ── Per-page sub-hero lede text ──────────────────────────────
    ledes: {
        about:        "Cancer cell biology &amp; drug delivery researcher, leading molecular oncology projects and collaborating across UAEU, NYU Abu Dhabi, and the University of Sharjah.",
        projects:     "Active work across cancer cell biology, nanomedicine, and bioinformatics. Some are published, some ongoing in the lab.",
        publications: "Peer-reviewed output across cancer biology, drug delivery, and nanomedicine. Updated automatically from Scholar and Scopus.",
        blog:         "Lab notes, research reflections, and the occasional write-up from conferences and collaborations.",
        talks:        "Conference presentations, lab visits, and the awards that have shaped the work. Slides and details are linked where I have them.",
        contact:      "The fastest way to reach me. Below the form there are short notes for research collaborators, supervision enquiries, and press.",
        research:     "The longer version of the work I lead, the questions I want to answer, and where I would like to take cancer biology next.",
        arc:          "The longer story of how I got from pharmacy to leading molecular oncology projects at HBRC, told as a sequence of moments rather than a CV."
    },

    // ── Scrollytelling research arc (rendered on arc.html) ───────
    arc: {
        kicker: "Research arc",
        h1Front: "From pharmacy bench to",
        h1Accent: "molecular oncology",
        intro: "The research statement is the short version. This page is the long way around. Five chapters, in order, told as a sequence of moments rather than a CV. Scroll at your own pace.",
        chapters: [
            {
                key: "origin",
                frame: "origin",
                kicker: "Chapter 1 · 2016 to 2021",
                title: "Pharmacy training, with one curiosity I could not let go of.",
                body: [
                    "I did my BSc in Pharmacy at Al Ain University. Five years of medicinal chemistry, pharmacokinetics, and clinical pharmacy. Comfortable around drugs as objects, around the language of chemistry and pharmacology. The pieces fit, but the question that followed me was a step upstream of the dispensing counter.",
                    "Why do most cancer therapies hit healthy tissue alongside the tumour? Why do promising compounds fail when they meet a real cancer cell line? Those questions are what eventually pulled me into the lab and into formulation work."
                ],
                milestone: {
                    label: "BSc Pharmacy",
                    sub: "Al Ain University, College of Pharmacy"
                }
            },
            {
                key: "msc",
                frame: "sieve",
                kicker: "Chapter 2 · 2021 to 2023",
                title: "An MSc, a thesis, and the controlled-release problem.",
                body: [
                    "I started a postgraduate scholarship at Al Ain University in 2021, working under supervisors with deep formulation experience. The brief was practical. Build controlled-release systems that actually behave the way the dissolution curves promise.",
                    "The first-author work on theophylline controlled-release matrix systems with poloxamer 407 and HPMC came out in <em>Polymers</em> in 2024. A second paper followed on hydration forms and polymer grades, also first-author. Both papers shipped during my MSc, and both got cited by formulation groups I had only read about during coursework.",
                    "That stretch is also when I learned what I actually like doing. Not just running experiments. Building the formulations that other people use, and being honest about why they fail."
                ],
                milestone: {
                    label: "MSc Pharmaceutical Sciences",
                    sub: "First-author papers in Polymers and Pharmaceuticals",
                    href: "https://doi.org/10.3390/polym16050643"
                }
            },
            {
                key: "lab",
                frame: "editorial",
                kicker: "Chapter 3 · 2023 to 2025",
                title: "Inside the HBRC lab as Research Supervisor.",
                body: [
                    "Since 2023 I have been Laboratory and Research Supervisor at the Health and Biomedical Research Center at Al Ain University. The job is exactly what it sounds like. Day-to-day supervision of analytical instruments, cell-culture lines, and the experimental design behind multiple projects across formulation, drug delivery, and molecular oncology.",
                    "I also train and guide postgraduate students through advanced cell-culture work, cytotoxic screening, and gene-knockout protocols. Watching them go from a clean cell-counting protocol to running their own combination-index experiments is most of the reason I stay in this role.",
                    "The collaborations have widened along the way. UAEU, NYU Abu Dhabi, and the University of Sharjah are now standing partners on several of the active projects."
                ],
                milestone: {
                    label: "HBRC, Al Ain University",
                    sub: "Lab &amp; Research Supervisor since 2023"
                }
            },
            {
                key: "now",
                frame: "network",
                kicker: "Chapter 4 · 2025 to 2026",
                title: "Cancer biology, nanomedicine, and a tight publishing run.",
                body: [
                    "The last 18 months have been the most productive stretch of my research life so far. First-author and senior-author work on inhalable nanoparticles for non-small cell lung cancer, on thymoquinone as a targeted cancer therapy, on synergistic ER-stress modulation with insulin potentiation, on ERK5 inhibitor discovery, and a review of large language models in drug delivery.",
                    "I am now spending most of my research time on three parallel threads. Cancer cell biology and gene-knockout studies of resistance mechanisms. Engineered nanoformulations for targeted delivery, especially inhalable platforms for lung cancer. And computational identification of therapeutic targets bridging bioinformatics with wet-lab validation.",
                    "All three threads share the same instinct as the controlled-release work. Build the thing that the next researcher will actually use at the bench."
                ],
                milestone: {
                    label: "Multiple first-author papers across 2025 to 2026",
                    sub: "Inhalable NSCLC nanoparticles · Thymoquinone · ERK5 inhibitors · LLMs in delivery"
                }
            },
            {
                key: "next",
                frame: "horizon",
                kicker: "Chapter 5 · Where this goes",
                title: "Collaborators welcome. PhD studies on the horizon.",
                body: [
                    "I am open to research collaborations across cancer cell biology, drug delivery, and nanomedicine. Wet-lab groups with cell-line panels, medicinal chemists with novel compound libraries, and bioinformatics teams with target-prediction pipelines all have a clear point of entry into the ongoing projects at HBRC.",
                    "I am also planning PhD studies in precision nanomedicine and targeted drug delivery, building on the molecular oncology projects I lead now. Strong methods groups in cancer biology and drug delivery are on the list.",
                    "If any of that fits your work, the fastest way to start a conversation is to email me directly."
                ],
                milestone: {
                    label: "Open for collaboration · PhD studies ahead",
                    sub: "Cancer biology · Nanomedicine · Targeted drug delivery",
                    href: "mailto:Molham.sakkal@gmail.com?subject=Research%20collaboration%20enquiry"
                }
            }
        ]
    },

    // ── Open-for-collaboration CTA block (rendered on index hero) ────
    // Mirrors Abdallah's phdCTA structure but reframed for an active
    // lab supervisor rather than an applicant. This is the primary
    // conversion goal of the home page.
    phdCTA: {
        ribbon:  "Open for collaboration",
        title:   "Lead a cancer biology or nanomedicine project together",
        body:    "I am leading active research at HBRC across cancer cell biology, gene-knockout studies, and engineered nanoformulations for targeted delivery. If your group works on cancer cell-line panels, medicinal chemistry libraries, computational target prediction, or wet-lab validation, I would like to hear from you. PhD students and visiting researchers also welcome.",
        primaryLabel: "Email me",
        primaryHref:  "mailto:Molham.sakkal@gmail.com?subject=Research%20collaboration%20enquiry&body=Hi%20Molham%2C%0A%0AI%20saw%20your%20website%20and%20wanted%20to%20discuss%20a%20potential%20collaboration.%0A%0A",
        secondaryLabel: "Read my research statement",
        secondaryHref:  "research.html",
        tertiaryLabel:  "See active projects",
        tertiaryHref:   "projects.html"
    },

    // ── "By the numbers" impact tiles (home page) ────────────────
    // First tile auto-updates via build_html.py from the weekly SerpApi pull.
    impactStats: [
        { num: "15",  label: "Publications",     sub: "peer-reviewed",                       numLiveSource: "total_documents" },
        { num: "112", label: "Citations",        sub: "across all work",                     numLiveSource: "total_citations" },
        { num: "6",   label: "h-index",          sub: "sustained impact" },
        { num: "🔬",  label: "Lab Supervisor",   sub: "HBRC · Al Ain University",            variant: "gold" },
        { num: "3+",  label: "Institutions",     sub: "UAEU · NYU AD · U. Sharjah" }
    ],

    // ── About page ────────────────────────────────────────────────
    about: {
        paragraphs: [
            "I hold a <strong>Bachelor's in Pharmacy</strong> and a <strong>Master's in Pharmaceutical Sciences</strong> from Al Ain University, where I specialized in drug delivery and formulation development. During my master's, I worked as a Research and Laboratory Assistant. That's when I really caught the research bug. Spending long hours with analytical instruments and cancer cell lines turned out to be more exciting than I expected.",
            "I'm now a <strong>Laboratory and Research Supervisor</strong> at the <strong>Health and Biomedical Research Center (HBRC)</strong>, where I lead research projects in molecular oncology, cancer cell biology, and drug delivery systems. I also train and guide postgraduate students in advanced cell culture techniques and experimental design.",
            "My collaborations span institutions like <strong>UAEU</strong>, <strong>NYU Abu Dhabi</strong>, and the <strong>University of Sharjah</strong>. I'm passionate about <em>bridging laboratory innovation with real-world therapeutic impact</em> as I plan my PhD studies."
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
            desc: "Enhancing treatment outcomes through drug-drug synergy. Evaluating combinations of cytotoxic agents across cancer cell lines to identify formulations that lower effective dose and reduce off-target toxicity.",
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
            needs: "Medicinal chemists with novel compound libraries welcome. Especially synthetic natural-product derivatives."
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
            title: "Engineered Nanoformulations for NSCLC",
            desc: "Engineering targeted delivery systems for improved therapeutic efficacy. Focus on inhalable nanoparticles for non-small cell lung cancer and smart chemotherapy platforms.",
            tech: ["Nanoparticles", "Drug Delivery", "Targeted Therapy", "NSCLC"],
            status: "Published · Saudi Pharmaceutical Journal · 2025",
            statusKind: "published",
            doi:   "10.1007/s44446-025-00046-y",
            venue: "Saudi Pharmaceutical Journal"
        },
        {
            n: "06",
            label: "Cancer · Targeted Therapy",
            title: "Thymoquinone in Targeted Cancer Therapy",
            desc: "Review of thymoquinone as a natural-product anticancer agent. Maps molecular mechanisms to clinical prospects and the formulation strategies that could move it closer to translation.",
            tech: ["Thymoquinone", "Natural Products", "Cancer", "Review"],
            status: "Published · International Journal of Molecular Sciences · 2025",
            statusKind: "published",
            doi:   "10.3390/ijms262211029",
            venue: "International Journal of Molecular Sciences"
        }
    ],

    // ── Blog ──────────────────────────────────────────────────────
    blog: [],

    // ── Talks, posters, presentations ─────────────────────────────
    // `kind`: 'hackathon' | 'poster' | 'talk' | 'workshop' | 'thesis'
    talks: [
        {
            date: "2025",
            year: 2025,
            kind: "talk",
            title: "Inhalable Nanoparticles for NSCLC Therapy",
            venue: "HBRC Research Forum · Al Ain University",
            desc:  "A walk-through of the inhalable nanoparticle platform we built for non-small cell lung cancer therapy, including formulation choice, in-vitro response across cell lines, and the open questions in translating the platform to in-vivo work."
        },
        {
            date: "2024",
            year: 2024,
            kind: "poster",
            title: "Theophylline Controlled-Release Matrix Systems",
            venue: "Pharmaceutical Sciences Symposium · Al Ain University",
            desc:  "Poster on the controlled-release matrix systems combining poloxamer 407, stearyl alcohol, and HPMC. Walks through dissolution profiles, hydration form effects, and the formulation choices that survived re-validation."
        },
        {
            date: "2023",
            year: 2023,
            kind: "thesis",
            title: "MSc Thesis Defence — Pharmaceutical Sciences",
            venue: "Al Ain University, College of Pharmacy",
            desc:  "Public defence of the MSc thesis on drug delivery and formulation development. First-author papers in Polymers and Pharmaceuticals followed in the year after."
        },
        {
            date: "2023 onward",
            year: 2023,
            kind: "workshop",
            title: "Postgraduate Cell-Culture Training",
            venue: "Health and Biomedical Research Center, Al Ain University",
            desc:  "Recurring hands-on training I run for postgraduate students on advanced cell-culture techniques, cytotoxic screening, and the experimental design behind combination-index work. Now in its third cohort."
        }
    ],

    // ── Research statement / vision (research.html) ──────────────
    research: {
        kicker: "Research statement",
        h1Front:  "Where I want to take",
        h1Accent: "cancer biology next",
        intro: "I want to spend the next stretch of my career building drug-delivery and cancer-cell-biology platforms that hit tumour tissue harder and healthy tissue less. The papers below show how the focus formed; the section after them describes what a collaboration or PhD with me looks like.",
        sections: [
            {
                kicker: "Origin",
                title: "From pharmacy bench to formulation work",
                body: [
                    "I trained as a pharmacist at Al Ain University, then ran headlong into a Master's in pharmaceutical sciences with a heavy formulation focus. The MSc gave me first-author papers in <em>Polymers</em> and <em>Pharmaceuticals</em> on controlled-release matrix systems, plus a second paper on hydration forms and polymer grades. Both projects shared one instinct. Stop trusting the dissolution curve until you have rebuilt it from scratch with fresh excipients.",
                    "That instinct still shapes everything I do at HBRC. A formulation that looks clean in a single dissolution apparatus is not yet a formulation. Repeat the experiment with hydrated polymer, with a different grade, with a different cell line, and only then can we start arguing about whether the platform is real."
                ]
            },
            {
                kicker: "What I learned",
                title: "Three habits I keep going back to",
                body: [
                    "<strong>1. Formulation first, then cell line.</strong> A drug-delivery system is only as good as the formulation underneath it. I spend more time on polymer selection, excipient screening, and physical characterisation than on the final cell-viability readout.",
                    "<strong>2. Cancer cells are not interchangeable.</strong> Every project at HBRC validates on more than one cell line because the cell line that says yes the loudest is often the one that says yes to almost everything. Multi-line validation is non-negotiable now.",
                    "<strong>3. Train the next person.</strong> A research group dies the moment it stops teaching. Most weeks I spend several hours walking postgrads through cytotoxic screening, combination-index analysis, and the experimental design choices behind the projects we run. The lab gets stronger every cohort."
                ]
            },
            {
                kicker: "Current focus",
                title: "Three threads I am pulling on now",
                body: [
                    "<strong>Cancer cell biology and resistance mechanisms.</strong> Gene knockout studies of chemoresistance pathways across multiple cancer cell lines, with the explicit goal of finding druggable vulnerabilities that survive multi-line validation. The Thymoquinone review and the ER-stress / insulin-potentiation work both fed this thread.",
                    "<strong>Engineered nanoformulations for targeted delivery.</strong> Building inhalable nanoparticle platforms for non-small cell lung cancer (the 2025 <em>Saudi Pharmaceutical Journal</em> paper is the first instalment), plus smarter chemotherapy carriers more broadly. Targeted delivery as a way to cut off-target toxicity rather than as a marketing line.",
                    "<strong>Bioinformatics-to-bench pipelines.</strong> Computational identification of therapeutic targets in cancer genomics, paired with wet-lab validation in our own cell-line panel. The hardest part of this work is closing the loop between a prediction and a clean cytotoxic readout. I want to make that loop shorter."
                ]
            },
            {
                kicker: "Collaboration vision",
                title: "What working with me looks like",
                body: [
                    "I run an active wet lab at HBRC and supervise a small group of postgraduate students. Collaborations work best when they bring something the lab does not already have. A novel compound library from a medicinal-chemistry group. A computational target-prediction pipeline that needs in-vitro validation. A clinical specimen set with the regulatory paperwork already cleared.",
                    "What I bring back is a working wet lab, multi-cell-line validation, formulation expertise on the delivery side, and a steady cadence of papers that close the loop between idea and validated readout. We have published with UAEU, NYU Abu Dhabi, and the University of Sharjah, so the cross-institution paperwork is a solved problem here.",
                    "I am also planning PhD studies in precision nanomedicine and targeted drug delivery, building on the work I lead today. If you supervise a group that touches any of the threads above, I would like to talk."
                ]
            },
            {
                kicker: "If we should talk",
                title: "Reasons to email me",
                body: [
                    "If your group works on cancer cell biology, targeted drug delivery, or computational target prediction, and you want a wet-lab partner who can validate fast and write up cleanly, that is the strongest match. Even a 20-minute call about whether we would be a fit is worth it.",
                    "I am also happy to be told my framing is off. Cancer biology is wide enough that there is always a sharper angle on any given problem. The right collaborator will sharpen the work."
                ]
            }
        ],
        finalCTAText: "Email Molham →",
        finalCTAHref: "mailto:Molham.sakkal@gmail.com?subject=Research%20collaboration%20enquiry&body=Hi%20Molham%2C%0A%0AI%20read%20your%20research%20statement%20and%20wanted%20to%20discuss%20a%20potential%20collaboration.%0A%0A"
    },

    // ── Contact page (contact.html) ───────────────────────────────
    contact: {
        kicker: "Get in touch",
        h1Front:  "Let's",
        h1Accent: "talk",
        intro: "I read every email. Below the form there are short notes for research collaborators, supervision enquiries, and press, plus the direct ways to reach me.",
        formAction: "https://formspree.io/f/REPLACE_WITH_FORMSPREE_ID",
        formNote: "The contact form is not yet wired to a Formspree endpoint. Until then please email me directly.",
        directEmail: "Molham.sakkal@gmail.com",
        cvHref: "mailto:Molham.sakkal@gmail.com?subject=CV%20request",
        blocks: [
            {
                icon: "🤝",
                title: "Research collaborators",
                body:  "Open to collaborations on cancer cell biology, drug delivery, nanomedicine, and cancer bioinformatics. If you have a novel compound library, a target-prediction pipeline, or a clinical specimen set that needs wet-lab validation, I am genuinely interested. See the <a href=\"projects.html\">Ongoing Research</a> page for what is currently active at HBRC."
            },
            {
                icon: "🎓",
                title: "Supervision &amp; postgrad enquiries",
                body:  "I supervise postgraduate students at HBRC across cell-culture, cytotoxic screening, combination-index analysis, and experimental design for drug delivery work. If you are an MSc or PhD student looking for a wet-lab project in cancer biology or targeted delivery, write to me with your CV and a one-paragraph statement of what you want to learn."
            },
            {
                icon: "✉️",
                title: "Journalists &amp; press",
                body:  "Happy to talk about cancer cell biology, targeted drug delivery, inhalable nanoparticles for lung cancer, and what hands-on lab supervision looks like at a research centre in the UAE. Reach out via the form or directly by email."
            }
        ],
        responseTimeNote: "Usually within 48 hours, faster on weekdays in Gulf Standard Time."
    },

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
