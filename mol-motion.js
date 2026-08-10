/* mol-motion.js · additive animation behaviours
 *
 * Loaded AFTER scripts.js. Never touches SITE_CONFIG, data flow, or any
 * machine contract; it only reads numbers already present in the DOM and
 * animates them the first time they scroll into view.
 *
 * 1. Count-up on metric numerals:
 *      - home:         .impact-num           (impact tiles)
 *      - publications: #m-total #m-cites #m-h (metrics dashboard)
 *    Values like "15", "112", "3+" animate from 0; non-numeric values
 *    ("HBRC") are left alone. serpapi.v1.js may overwrite the spans with
 *    fresher fetched values afterwards; last write wins either way.
 *
 * 2. Respects prefers-reduced-motion: no animation, values stay as baked.
 */
(function () {
    'use strict';

    var reduce = false;
    try {
        reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) { /* matchMedia unavailable: animate */ }

    /* Ease-out cubic, mirrors the site's --ease feel */
    function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

    function countUp(el) {
        var raw = (el.textContent || '').trim();
        var m = raw.match(/^(\d[\d,]*)(.*)$/);
        if (!m) return;                       /* non-numeric: leave alone */
        var target = parseInt(m[1].replace(/,/g, ''), 10);
        if (isNaN(target) || target <= 0) return;
        var suffix = m[2] || '';
        var dur = Math.min(1100, 500 + target * 4);
        var t0 = null;

        function frame(ts) {
            if (t0 === null) t0 = ts;
            var p = Math.min(1, (ts - t0) / dur);
            var val = Math.round(easeOut(p) * target);
            el.textContent = String(val) + suffix;
            if (p < 1) {
                requestAnimationFrame(frame);
            } else {
                el.textContent = String(target) + suffix;
            }
        }
        el.textContent = '0' + suffix;
        requestAnimationFrame(frame);
    }

    function init() {
        var targets = [];
        document.querySelectorAll('.impact-num').forEach(function (el) { targets.push(el); });
        ['m-total', 'm-cites', 'm-h'].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) targets.push(el);
        });
        if (!targets.length) return;

        if (reduce || !('IntersectionObserver' in window)) return; /* leave baked values */

        var seen = new WeakSet();
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting && !seen.has(entry.target)) {
                    seen.add(entry.target);
                    countUp(entry.target);
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.4 });

        targets.forEach(function (el) { io.observe(el); });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
