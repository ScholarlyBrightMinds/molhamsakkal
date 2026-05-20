/* research-map.js — Force-directed research-concept map.
 *
 * Reads the JSON payload baked into the page by build_research_map.py and
 * runs a small spring-physics simulation on top of the static SVG so the
 * layout settles into a clean shape, then hands over to mouse/touch
 * interactions (hover highlight + drag).
 *
 * Pure vanilla JS, no D3 / no dependencies. The simulation uses Verlet-ish
 * integration with three forces:
 *   1. Centering pull on the "me" node (it stays at canvas center)
 *   2. Repulsion between every pair of nodes (Coulomb-like 1/r²)
 *   3. Spring on each edge (Hooke's law, rest length scaled by node sizes)
 *
 * Respects prefers-reduced-motion: skips animation and renders the static
 * SVG layout as-is.
 */
(function () {
    'use strict';

    const SVG_NS = 'http://www.w3.org/2000/svg';

    function init() {
        const section = document.querySelector('section.research-map');
        if (!section) return;

        const dataNode = section.querySelector('script#research-map-data');
        const svg      = section.querySelector('svg.research-map-svg');
        if (!dataNode || !svg) return;

        let payload;
        try {
            payload = JSON.parse(dataNode.textContent);
        } catch (e) {
            console.warn('[research-map] could not parse data payload:', e);
            return;
        }

        const viewBox = (svg.getAttribute('viewBox') || '0 0 960 520').split(' ').map(Number);
        const W = viewBox[2] || 960;
        const H = viewBox[3] || 520;

        // Build node list. Each node carries its current position, velocity,
        // and a back-reference to its <g> element.
        const nodeById = new Map();
        const nodes    = [];

        function addNode(n, kind, radius) {
            const g = svg.querySelector(`g.rm-node[data-id="${cssEscape(n.id)}"]`);
            if (!g) return null;
            // Pull initial position from the static SVG transform
            const m = (g.getAttribute('transform') || '').match(
                /translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)/
            );
            const x = m ? parseFloat(m[1]) : W / 2;
            const y = m ? parseFloat(m[2]) : H / 2;
            const node = {
                id: n.id,
                kind,
                label: n.label,
                radius,
                x, y, vx: 0, vy: 0,
                fx: null, fy: null,           // pinned position when dragging
                el: g,
            };
            nodeById.set(n.id, node);
            nodes.push(node);
            return node;
        }

        addNode(payload.center, 'center', 56);
        for (const c of payload.concepts || []) {
            addNode(c, 'concept', 36 + Math.min(8, (c.score || 0) * 8));
        }
        for (const t of payload.topics || []) {
            addNode(t, 'topic', 24 + Math.min(10, (t.count || 0) * 1.4));
        }

        // Build edge list with adjacency for quick "neighbours of X" lookups
        const edges = [];
        const neighbours = new Map();
        for (const e of payload.edges || []) {
            const a = nodeById.get(e.a);
            const b = nodeById.get(e.b);
            if (!a || !b) continue;
            const el = svg.querySelector(
                `line.rm-edge[data-a="${cssEscape(e.a)}"][data-b="${cssEscape(e.b)}"]`
            );
            const edge = { a, b, weight: e.weight || 0.5, el };
            edges.push(edge);
            if (!neighbours.has(a.id)) neighbours.set(a.id, new Set());
            if (!neighbours.has(b.id)) neighbours.set(b.id, new Set());
            neighbours.get(a.id).add(b.id);
            neighbours.get(b.id).add(a.id);
        }

        // Pin the "me" node so the layout stays centred
        const meNode = nodeById.get('me');
        if (meNode) {
            meNode.fx = W / 2;
            meNode.fy = H / 2;
        }

        // The server-baked static positions in build_research_map.py
        // already give a clean concentric layout (concepts in an inner
        // ring, topics in an outer ring clustered near their parent
        // concept). The simulation is only used while the user is
        // dragging — to gently rebalance around the dragged node. On
        // load we just attach interactions and call it done.
        wireInteractions(svg, nodes, edges, nodeById, neighbours);

        // Simulation parameters used while dragging.
        const params = {
            repulsion:   6000,
            spring:      0.045,
            damping:     0.84,
            centerPull:  0.008,
            maxStep:     6,
            iters:       0,     // no auto-animation
        };

        let frame = 0;
        let dragging = null;
        let simRunning = false;

        function ensureSim() {
            if (simRunning) return;
            simRunning = true;
            requestAnimationFrame(step);
        }

        function step() {
            // 1. Reset force accumulator
            for (const n of nodes) { n.fx_a = 0; n.fy_a = 0; }

            // 2. Repulsion (O(n²) — fine at this scale)
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const a = nodes[i], b = nodes[j];
                    let dx = a.x - b.x, dy = a.y - b.y;
                    let d2 = dx * dx + dy * dy;
                    if (d2 < 1) { d2 = 1; dx = 1; dy = 0; }
                    const f = params.repulsion / d2;
                    const d  = Math.sqrt(d2);
                    const fx = (dx / d) * f, fy = (dy / d) * f;
                    a.fx_a += fx; a.fy_a += fy;
                    b.fx_a -= fx; b.fy_a -= fy;
                }
            }

            // 3. Springs along edges. Rest length depends on edge kind:
            //    center→concept stays close (concentric ring), topic→concept
            //    sits further out so the second ring is visibly outside the
            //    first one.
            for (const e of edges) {
                const a = e.a, b = e.b;
                const dx = b.x - a.x, dy = b.y - a.y;
                const d = Math.sqrt(dx * dx + dy * dy) || 1;
                const isCenterEdge = (a.kind === 'center' || b.kind === 'center');
                const baseRest = isCenterEdge ? 130 : 95;
                const rest = a.radius + b.radius + baseRest;
                const f = (d - rest) * params.spring;
                const fx = (dx / d) * f, fy = (dy / d) * f;
                a.fx_a += fx; a.fy_a += fy;
                b.fx_a -= fx; b.fy_a -= fy;
            }

            // 4. Weak pull toward canvas centre
            for (const n of nodes) {
                n.fx_a += (W / 2 - n.x) * params.centerPull;
                n.fy_a += (H / 2 - n.y) * params.centerPull;
            }

            // 5. Integrate with damping + step clamp
            for (const n of nodes) {
                if (n.fx !== null && n.fy !== null) {
                    n.x = n.fx; n.y = n.fy; n.vx = n.vy = 0;
                    continue;
                }
                n.vx = (n.vx + n.fx_a) * params.damping;
                n.vy = (n.vy + n.fy_a) * params.damping;
                const step = Math.hypot(n.vx, n.vy);
                if (step > params.maxStep) {
                    n.vx *= params.maxStep / step;
                    n.vy *= params.maxStep / step;
                }
                n.x += n.vx; n.y += n.vy;

                // Soft viewport clamp so labels don't escape the SVG
                const pad = n.radius + 4;
                n.x = Math.max(pad, Math.min(W - pad, n.x));
                n.y = Math.max(pad, Math.min(H - pad, n.y));
            }

            paint();
            frame++;
            if (frame < params.iters || dragging) {
                requestAnimationFrame(step);
            } else {
                simRunning = false;
            }
        }

        function paint() {
            for (const n of nodes) {
                n.el.setAttribute('transform', `translate(${n.x.toFixed(1)} ${n.y.toFixed(1)})`);
            }
            for (const e of edges) {
                if (!e.el) continue;
                e.el.setAttribute('x1', e.a.x.toFixed(1));
                e.el.setAttribute('y1', e.a.y.toFixed(1));
                e.el.setAttribute('x2', e.b.x.toFixed(1));
                e.el.setAttribute('y2', e.b.y.toFixed(1));
            }
        }

        // ── Interactions ───────────────────────────────────────────
        function ptFromEvent(evt) {
            const pt = svg.createSVGPoint();
            const t = evt.touches ? evt.touches[0] : evt;
            pt.x = t.clientX;
            pt.y = t.clientY;
            const ctm = svg.getScreenCTM();
            if (!ctm) return { x: 0, y: 0 };
            const inv = ctm.inverse();
            const local = pt.matrixTransform(inv);
            return { x: local.x, y: local.y };
        }

        function onPointerDown(evt) {
            const target = evt.target.closest('g.rm-node');
            if (!target) return;
            const id = target.getAttribute('data-id');
            if (id === 'me') return;
            const node = nodeById.get(id);
            if (!node) return;
            evt.preventDefault();
            dragging = node;
            target.classList.add('rm-node--dragging');
            ensureSim();
        }

        function onPointerMove(evt) {
            if (!dragging) return;
            const p = ptFromEvent(evt);
            dragging.fx = p.x;
            dragging.fy = p.y;
        }

        function onPointerUp() {
            if (!dragging) return;
            dragging.el.classList.remove('rm-node--dragging');
            dragging.fx = dragging.fy = null;
            dragging = null;
        }

        svg.addEventListener('mousedown',  onPointerDown);
        svg.addEventListener('touchstart', onPointerDown, { passive: false });
        window.addEventListener('mousemove', onPointerMove);
        window.addEventListener('touchmove', onPointerMove, { passive: false });
        window.addEventListener('mouseup',   onPointerUp);
        window.addEventListener('touchend',  onPointerUp);

        wireInteractions(svg, nodes, edges, nodeById, neighbours);
    }

    /** Hover/focus highlighting — independent of the simulation. */
    function wireInteractions(svg, nodes, edges, nodeById, neighbours) {
        function highlight(id) {
            const adj = neighbours.get(id) || new Set();
            for (const n of nodes) {
                const active = (n.id === id) || adj.has(n.id);
                n.el.classList.toggle('rm-node--dim', !active && id !== null);
                n.el.classList.toggle('rm-node--focus', n.id === id);
                n.el.classList.toggle('rm-node--neighbour', active && n.id !== id);
            }
            for (const e of edges) {
                if (!e.el) continue;
                const isAdj = (e.a.id === id || e.b.id === id);
                e.el.classList.toggle('rm-edge--dim',   !isAdj && id !== null);
                e.el.classList.toggle('rm-edge--focus', isAdj);
            }
        }

        for (const n of nodes) {
            n.el.setAttribute('tabindex', '0');
            n.el.addEventListener('mouseenter', () => highlight(n.id));
            n.el.addEventListener('focus',      () => highlight(n.id));
        }
        svg.addEventListener('mouseleave', () => highlight(null));
        svg.addEventListener('focusout',   (e) => {
            // Only clear when focus leaves the SVG entirely
            if (!svg.contains(e.relatedTarget)) highlight(null);
        });
    }

    /** Minimal CSS.escape polyfill for the data-id values (alphanumeric +
     *  hyphen + underscore in practice, so this is safe). */
    function cssEscape(s) {
        if (window.CSS && CSS.escape) return CSS.escape(s);
        return String(s).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
