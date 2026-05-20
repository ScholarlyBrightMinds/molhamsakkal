/* arc.js — Scrollytelling driver for arc.html.
 *
 * Two jobs:
 *   1. Watch the .arc-step sections via IntersectionObserver and toggle
 *      `.is-active` on the matching .arc-frame in the sticky left stage,
 *      plus on the step itself for the dim/un-dim effect.
 *   2. Update the .arc-hero-progress fill bar with how far the reader has
 *      scrolled through the chapter list.
 *
 * No deps. Respects prefers-reduced-motion (the dim transition is still
 * applied; only the SVG decorative animations honour the system
 * preference, via CSS @media queries).
 */
(function () {
    'use strict';

    function init() {
        const steps  = document.querySelectorAll('.arc-step');
        const frames = document.querySelectorAll('.arc-frame');
        const fill   = document.querySelector('.arc-hero-progress-fill');
        if (!steps.length || !frames.length) return;

        const framesById = new Map();
        frames.forEach(f => framesById.set(f.getAttribute('data-frame'), f));

        // Activate the first frame by default so the stage isn't blank on
        // initial paint before any scroll has happened.
        const firstStep = steps[0];
        const firstFrameId = firstStep && firstStep.getAttribute('data-arc-frame');
        if (firstFrameId && framesById.has(firstFrameId)) {
            framesById.get(firstFrameId).classList.add('is-active');
        }

        // Track which step is currently "most in view"
        let active = firstStep || null;
        if (active) active.classList.add('is-active');

        const visibility = new Map();  // step -> intersectionRatio

        const io = new IntersectionObserver((entries) => {
            for (const e of entries) {
                visibility.set(e.target, e.intersectionRatio);
            }
            // Pick the step with the highest visibility ratio
            let best = null;
            let bestRatio = 0;
            for (const [step, ratio] of visibility) {
                if (ratio > bestRatio) {
                    best = step;
                    bestRatio = ratio;
                }
            }
            if (best && best !== active) {
                if (active) active.classList.remove('is-active');
                best.classList.add('is-active');
                active = best;

                // Swap the active stage frame
                const fid = best.getAttribute('data-arc-frame');
                frames.forEach(f => f.classList.remove('is-active'));
                if (fid && framesById.has(fid)) {
                    framesById.get(fid).classList.add('is-active');
                }
            }
            // Update progress bar
            if (fill) {
                const all = Array.from(steps);
                const idx = active ? all.indexOf(active) : 0;
                const pct = ((idx + 1) / all.length) * 100;
                fill.style.width = pct.toFixed(1) + '%';
            }
        }, {
            // Trigger when each section's centre crosses the middle of the
            // viewport. The negative top + bottom margins create a band of
            // ~40% viewport height that the "active" step must be in.
            rootMargin: '-30% 0px -30% 0px',
            threshold: [0, 0.15, 0.3, 0.5, 0.75, 1],
        });

        steps.forEach(s => io.observe(s));
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
