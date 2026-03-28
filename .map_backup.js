// ============================================================
// MAP INTEGRATION BACKUP — reintegrate into index.html after pull
// ============================================================
// HOW TO REINTEGRATE:
//   1. CSS block → paste inside <style> tag (before closing </style>)
//   2. HTML block → paste after the death screen div, before the main layout div
//   3. updateUI addition → merge into existing updateUI's location block
//   4. JS block → paste inside <script> tag, before the window.onload / sendAction functions
//   5. sendAction addition → paste at top of sendAction, after the actionText trim check
// ============================================================


// ── [1] CSS — paste inside <style> ──────────────────────────────────────────

/*
        /* ── WORLD MAP STYLES ── */
        #world-map-modal {
            display: none;
            position: fixed; inset: 0;
            background: rgba(0,0,0,0.97);
            z-index: 90;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(12px);
        }
        #world-map-modal.open { display: flex; }

        #map-container {
            position: relative;
            width: 100%;
            max-width: 900px;
            height: 560px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(139,92,246,0.3);
            box-shadow: 0 0 60px rgba(107,33,168,0.2);
        }

        #map-canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
        #map-svg    { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }

        .map-node { cursor: pointer; }
        .map-node:hover .node-circle { filter: drop-shadow(0 0 14px var(--node-glow)); }
        .node-circle { transition: r 0.2s ease; }
        .node-label  { font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: 0.08em; fill: #c4b5fd; }
        .node-sublabel { font-family: 'Cinzel', serif; font-size: 8px; fill: #6b5a8a; letter-spacing: 0.05em; }

        @keyframes pulse-anim {
            0%, 100% { opacity: 0.35; }
            50%       { opacity: 0.9;  }
        }
        .pulse-ring { animation: pulse-anim 2s ease-in-out infinite; }

        @keyframes dashFlow {
            to { stroke-dashoffset: -26; }
        }
        .path-flow { stroke-dasharray: 6 20; animation: dashFlow 2.5s linear infinite; }

        #map-tooltip {
            position: absolute;
            background: rgba(8,4,18,0.97);
            border: 1px solid rgba(139,92,246,0.5);
            border-radius: 8px;
            padding: 12px 14px;
            width: 185px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s;
            z-index: 10;
            font-family: 'Cinzel', serif;
        }
        #map-tooltip.visible { opacity: 1; }
        #map-tooltip .tt-name { font-size: 11px; color: #e9d5ff; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 3px; }
        #map-tooltip .tt-type { font-size: 9px; color: #7c3aed; margin-bottom: 7px; font-style: italic; letter-spacing: 0.06em; }
        #map-tooltip .tt-desc { font-size: 11px; color: #9ca3af; line-height: 1.5; font-family: 'Crimson Text', serif; }
        #map-tooltip .tt-cta        { margin-top: 9px; font-size: 9px; color: #a855f7; letter-spacing: 0.08em; }
        #map-tooltip .tt-cta.locked { color: #ef4444; }
        .map-node-locked { cursor: not-allowed !important; }
        @keyframes lockShake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-4px); }
            40%, 80% { transform: translateX(4px); }
        }
        .lock-shake { animation: lockShake 0.35s ease; }

        #map-loc-bar {
            position: absolute;
            bottom: 14px; left: 50%; transform: translateX(-50%);
            background: rgba(8,4,18,0.9);
            border: 1px solid rgba(139,92,246,0.3);
            border-radius: 6px; padding: 5px 18px;
            font-family: 'Cinzel', serif; font-size: 9px;
            color: #6d28d9; letter-spacing: 0.2em; text-transform: uppercase;
            white-space: nowrap; z-index: 5;
        }
        #map-loc-bar span { color: #c4b5fd; margin-left: 6px; }

        .region-label {
            position: absolute;
            font-family: 'Cinzel', serif; font-size: 11px;
            letter-spacing: 0.35em; color: rgba(107,33,168,0.35);
            text-transform: uppercase; font-weight: bold; pointer-events: none;
        }
*/


// ── [2] HTML — paste after death screen, before main layout div ─────────────

/*
    <!-- ── WORLD MAP MODAL ── -->
    <div id="world-map-modal">
        <div class="w-full max-w-4xl flex justify-between items-end mb-4 px-4">
            <div class="text-purple-500 title-font tracking-[0.5em] text-sm uppercase">Atlas of the Shattered World</div>
            <button onclick="toggleMap()" class="text-gray-500 hover:text-red-400 title-font text-xs tracking-widest uppercase transition-colors">[PRESS M TO CLOSE]</button>
        </div>

        <div id="map-container">
            <canvas id="map-canvas"></canvas>

            <div class="region-label" style="top:8%;left:8%">Imperial Ruins</div>
            <div class="region-label" style="bottom:12%;left:8%">The Sunken Quarter</div>
            <div class="region-label" style="top:8%;right:6%">Void Wastes</div>
            <div class="region-label" style="bottom:12%;right:6%">Saltmarsh</div>

            <svg id="map-svg" viewBox="0 0 900 560" preserveAspectRatio="xMidYMid meet"></svg>

            <div id="map-tooltip">
                <div class="tt-name" id="tt-name"></div>
                <div class="tt-type" id="tt-type"></div>
                <div class="tt-desc"  id="tt-desc"></div>
                <div class="tt-cta" id="tt-cta">↗ Click to fast travel</div>
            </div>

            <div id="map-loc-bar">Current Location: <span id="map-cur-loc">---</span></div>
        </div>
    </div>
*/


// ── [3] updateUI addition — merge into the existing location block ───────────
// Find: if (gameState.location) { ... } and add these two lines inside it:

/*
                const locBar = document.getElementById('map-cur-loc');
                if (locBar) locBar.textContent = gameState.location.replace(/_/g, ' ');
                syncMapLocation(gameState.location);
*/


// ── [4] JS — paste inside <script>, before window.onload ────────────────────

const MAP_NODES = [
    {
        id: 'ashen_courtyard', label: ['Ashen', 'Courtyard'], icon: '🏛',
        x: 420, y: 300, type: 'Hub',
        desc: 'Central ruins of the old imperial district. A safe haven between paths.',
        color: { fill:'#1e0f3a', stroke:'#7c3aed', glow:'#9333ea' }
    },
    {
        id: 'ruined_keep', label: ['Ruined', 'Keep'], icon: '🏰',
        x: 260, y: 185, type: 'Dungeon',
        desc: 'A collapsed fortification haunted by the spirits of fallen soldiers.',
        color: { fill:'#3b0f0f', stroke:'#991b1b', glow:'#dc2626' }
    },
    {
        id: 'throne_vault', label: ['Throne', 'Vault'], icon: '💎',
        x: 120, y: 90, type: 'Boss Area', locked: true, requires: 'Vault Key',
        desc: 'The sealed vault beneath the old throne. Great danger awaits those who enter.',
        color: { fill:'#12093a', stroke:'#4338ca', glow:'#818cf8' }
    },
    {
        id: 'sunken_library', label: ['Sunken', 'Library'], icon: '📚',
        x: 230, y: 430, type: 'Exploration',
        desc: 'Ancient tomes half-submerged in void water. Knowledge and peril in equal measure.',
        color: { fill:'#071f10', stroke:'#065f46', glow:'#10b981' }
    },
    {
        id: 'void_bridge', label: ['Void', 'Bridge'], icon: '🌉',
        x: 570, y: 300, type: 'Transit',
        desc: 'A stone bridge arcing over the void rift. Connects the ruins to the east.',
        color: { fill:'#0c1a3a', stroke:'#1d4ed8', glow:'#60a5fa' }
    },
    {
        id: 'saltmarsh_gate', label: ['Saltmarsh', 'Gate'], icon: '⛩',
        x: 720, y: 300, type: 'Town Gate',
        desc: 'Entry to the Saltmarsh settlement. Guarded but welcoming to those with coin.',
        color: { fill:'#1e0f3a', stroke:'#7c3aed', glow:'#a78bfa' }
    },
    {
        id: 'the_ashen_flagon', label: ['Ashen', 'Flagon'], icon: '🍺',
        x: 690, y: 430, type: 'Tavern',
        desc: 'A dimly lit tavern. Rest, buy provisions, and hear rumors from passing travelers.',
        color: { fill:'#271300', stroke:'#92400e', glow:'#f59e0b' }
    },
    {
        id: 'saltmarsh_market', label: ['Market', 'Square'], icon: '⚖',
        x: 800, y: 430, type: 'Shop',
        desc: 'Merchants trade weapons, armor, and rare relics salvaged from the ruins.',
        color: { fill:'#0f1f07', stroke:'#3f6212', glow:'#84cc16' }
    },
    {
        id: 'void_wastes_edge', label: ['Void', 'Wastes'], icon: '⚠',
        x: 710, y: 150, type: 'Danger Zone', danger: true,
        desc: 'The edge of pure void corruption. Extremely dangerous. Rewards are unknown.',
        color: { fill:'#250000', stroke:'#7f1d1d', glow:'#ef4444' }
    },
];

const MAP_EDGES = [
    ['ashen_courtyard', 'ruined_keep'],
    ['ashen_courtyard', 'sunken_library'],
    ['ashen_courtyard', 'void_bridge'],
    ['ruined_keep',     'throne_vault'],
    ['void_bridge',     'saltmarsh_gate'],
    ['saltmarsh_gate',  'the_ashen_flagon'],
    ['saltmarsh_gate',  'saltmarsh_market'],
    ['void_bridge',     'void_wastes_edge'],
];

let isMapOpen = false;
let mapBuilt  = false;

function toggleMap() {
    const modal = document.getElementById('world-map-modal');
    isMapOpen = !isMapOpen;
    if (isMapOpen) {
        modal.classList.add('open');
        if (!mapBuilt) { buildMap(); mapBuilt = true; }
        if (gameState && gameState.location) syncMapLocation(gameState.location);
    } else {
        modal.classList.remove('open');
    }
}

document.addEventListener('keydown', e => {
    if (e.key.toLowerCase() === 'm' && document.activeElement !== input) {
        e.preventDefault();
        toggleMap();
    }
});

function svgEl(tag, attrs = {}) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
}

function buildMap() {
    drawMapCanvas();
    buildMapSVG();
}

function drawMapCanvas() {
    const canvas = document.getElementById('map-canvas');
    canvas.width  = canvas.offsetWidth  || 900;
    canvas.height = canvas.offsetHeight || 560;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#040210';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < 300; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const r = Math.random() * 1.3;
        const a = 0.1 + Math.random() * 0.7;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(200,180,255,${a})`;
        ctx.fill();
    }

    const patches = [
        { x: 220, y: 230, rx: 200, ry: 180, c: 'rgba(80,20,20,0.18)' },
        { x: 720, y: 360, rx: 200, ry: 160, c: 'rgba(20,20,70,0.18)' },
        { x: 420, y: 300, rx: 100, ry: 80,  c: 'rgba(60,20,100,0.2)'  },
        { x: 700, y: 140, rx: 140, ry: 100, c: 'rgba(80,5,5,0.28)'    },
        { x: 230, y: 440, rx: 140, ry: 100, c: 'rgba(10,50,25,0.2)'   },
    ];
    patches.forEach(p => {
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, Math.max(p.rx, p.ry));
        g.addColorStop(0, p.c);
        g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.save();
        ctx.scale(p.rx / Math.max(p.rx, p.ry), p.ry / Math.max(p.rx, p.ry));
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(
            p.x / (p.rx / Math.max(p.rx, p.ry)),
            p.y / (p.ry / Math.max(p.rx, p.ry)),
            Math.max(p.rx, p.ry), 0, Math.PI * 2
        );
        ctx.fill();
        ctx.restore();
    });

    ctx.strokeStyle = 'rgba(100,50,180,0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 8; i++) {
        ctx.beginPath();
        const sx = Math.random() * canvas.width;
        const sy = Math.random() * canvas.height;
        ctx.moveTo(sx, sy);
        let cx = sx, cy = sy;
        for (let j = 0; j < 4; j++) {
            cx += (Math.random() - 0.5) * 120;
            cy += (Math.random() - 0.5) * 120;
            ctx.lineTo(cx, cy);
        }
        ctx.stroke();
    }
}

function buildMapSVG() {
    const svg = document.getElementById('map-svg');
    svg.innerHTML = '';

    const defs = svgEl('defs');
    defs.innerHTML = `
        <marker id="map-arrow" viewBox="0 0 10 10" refX="8" refY="5"
                markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
                  stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </marker>
        <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
    `;
    svg.appendChild(defs);

    const edgeG = svgEl('g', { id: 'map-edges' });
    svg.appendChild(edgeG);

    MAP_EDGES.forEach(([aId, bId]) => {
        const na = MAP_NODES.find(n => n.id === aId);
        const nb = MAP_NODES.find(n => n.id === bId);
        if (!na || !nb) return;

        const base = svgEl('line', {
            x1: na.x, y1: na.y, x2: nb.x, y2: nb.y,
            stroke: 'rgba(139,92,246,0.18)',
            'stroke-width': '1.5',
            'stroke-dasharray': '4 6',
            fill: 'none',
        });
        edgeG.appendChild(base);

        const flow = svgEl('line', {
            x1: na.x, y1: na.y, x2: nb.x, y2: nb.y,
            stroke: 'rgba(139,92,246,0.55)',
            'stroke-width': '1',
            fill: 'none',
            class: 'path-flow',
        });
        flow.style.animationDuration = (2 + Math.random() * 2.5) + 's';
        edgeG.appendChild(flow);
    });

    const nodeG = svgEl('g', { id: 'map-nodes' });
    svg.appendChild(nodeG);

    const tooltip = document.getElementById('map-tooltip');
    const mapCont = document.getElementById('map-container');

    MAP_NODES.forEach(node => {
        const g = svgEl('g', { class: 'map-node', id: 'mnode-' + node.id });
        g.style.setProperty('--node-glow', node.color.glow);

        const pulse = svgEl('circle', {
            cx: node.x, cy: node.y, r: 26,
            fill: 'none', stroke: node.color.glow,
            'stroke-width': '1.2', opacity: '0',
            id: 'pulse-' + node.id,
        });
        g.appendChild(pulse);

        const glowDisc = svgEl('circle', {
            cx: node.x, cy: node.y, r: 30,
            fill: node.color.glow, opacity: '0.07',
            id: 'glowdisc-' + node.id,
        });
        g.appendChild(glowDisc);

        const circle = svgEl('circle', {
            cx: node.x, cy: node.y, r: 18,
            fill: node.color.fill, stroke: node.color.stroke,
            'stroke-width': node.locked ? '2' : '1.5',
            class: 'node-circle',
            id: 'bubble-' + node.id,
            opacity: node.locked ? '0.65' : '1',
        });
        g.appendChild(circle);

        const icon = svgEl('text', {
            x: node.x, y: node.y + 5,
            'text-anchor': 'middle', 'font-size': '13',
        });
        icon.textContent = node.icon;
        if (node.locked) icon.setAttribute('opacity', '0.45');
        g.appendChild(icon);

        if (node.locked) {
            const lock = svgEl('text', {
                x: node.x + 14, y: node.y - 11,
                'font-size': '9', 'text-anchor': 'middle',
            });
            lock.textContent = '🔒';
            g.appendChild(lock);
        }

        if (node.danger) {
            const dangerRing = svgEl('circle', {
                cx: node.x, cy: node.y, r: 22,
                fill: 'none', stroke: '#ef4444',
                'stroke-width': '0.8', opacity: '0.5',
            });
            const anim = svgEl('animate');
            anim.setAttribute('attributeName', 'r');
            anim.setAttribute('values', '22;28;22');
            anim.setAttribute('dur', '1.8s');
            anim.setAttribute('repeatCount', 'indefinite');
            dangerRing.appendChild(anim);
            g.appendChild(dangerRing);
        }

        node.label.forEach((line, i) => {
            const t = svgEl('text', {
                x: node.x, y: node.y + 32 + i * 13,
                'text-anchor': 'middle', class: 'node-label',
            });
            t.textContent = line;
            g.appendChild(t);
        });

        const sub = svgEl('text', {
            x: node.x, y: node.y + 32 + node.label.length * 13,
            'text-anchor': 'middle', class: 'node-sublabel',
        });
        sub.textContent = node.type.toUpperCase();
        g.appendChild(sub);

        if (node.locked) g.classList.add('map-node-locked');

        g.addEventListener('mouseenter', e => {
            document.getElementById('glowdisc-' + node.id).setAttribute('opacity', '0.22');
            const bub = document.getElementById('bubble-' + node.id);
            if (bub) bub.setAttribute('r', '21');
            document.getElementById('tt-name').textContent = node.label.join(' ');
            document.getElementById('tt-type').textContent = node.type;
            document.getElementById('tt-desc').textContent = node.desc;
            const cta = document.getElementById('tt-cta');
            if (node.locked) {
                cta.textContent = `🔒 Requires ${node.requires}`;
                cta.classList.add('locked');
            } else {
                cta.textContent = '↗ Click to fast travel';
                cta.classList.remove('locked');
            }
            posTooltip(e);
            tooltip.classList.add('visible');
        });
        g.addEventListener('mousemove', posTooltip);
        g.addEventListener('mouseleave', () => {
            if (node.id !== (gameState && gameState.location)) {
                document.getElementById('glowdisc-' + node.id).setAttribute('opacity', '0.07');
                const bub = document.getElementById('bubble-' + node.id);
                if (bub) bub.setAttribute('r', '18');
            }
            tooltip.classList.remove('visible');
        });

        g.addEventListener('click', () => {
            if (node.locked) {
                g.classList.add('lock-shake');
                setTimeout(() => g.classList.remove('lock-shake'), 350);
                toggleMap();
                const msg = document.createElement('p');
                msg.className = 'text-red-400 title-font text-xs tracking-widest msg-fade';
                msg.innerText = `🔒 ${node.label.join(' ')} is sealed — you need a ${node.requires} to enter.`;
                log.appendChild(msg);
                log.scrollTop = log.scrollHeight;
                return;
            }
            input.value = `move to ${node.id.replace(/_/g, ' ')}`;
            toggleMap();
            sendAction();
        });

        nodeG.appendChild(g);
    });

    function posTooltip(e) {
        const rect = mapCont.getBoundingClientRect();
        let tx = e.clientX - rect.left + 18;
        let ty = e.clientY - rect.top  - 70;
        if (tx + 200 > rect.width)  tx = e.clientX - rect.left - 208;
        if (ty < 0) ty = 8;
        tooltip.style.left = tx + 'px';
        tooltip.style.top  = ty + 'px';
    }
}

function syncMapLocation(locationId) {
    if (!mapBuilt) return;
    MAP_NODES.forEach(node => {
        const pulse = document.getElementById('pulse-'    + node.id);
        const glow  = document.getElementById('glowdisc-' + node.id);
        const bub   = document.getElementById('bubble-'   + node.id);
        if (node.id === locationId) {
            if (pulse) { pulse.setAttribute('opacity', '1'); pulse.classList.add('pulse-ring'); }
            if (glow)  glow.setAttribute('opacity', '0.28');
            if (bub)   bub.setAttribute('r', '21');
        } else {
            if (pulse) { pulse.setAttribute('opacity', '0'); pulse.classList.remove('pulse-ring'); }
            if (glow)  glow.setAttribute('opacity', '0.07');
            if (bub)   bub.setAttribute('r', '18');
        }
    });
}


// ── [5] sendAction addition — paste at top of sendAction after actionText trim ──
// (blocks typed movement to locked locations)

/*
            const lockedNodes = MAP_NODES.filter(n => n.locked);
            for (const node of lockedNodes) {
                const name = node.id.replace(/_/g, ' ');
                if (actionText.toLowerCase().includes(name)) {
                    input.value = '';
                    const msg = document.createElement('p');
                    msg.className = 'text-red-400 title-font text-xs tracking-widest msg-fade';
                    msg.innerText = `🔒 ${node.label.join(' ')} is sealed — you need a ${node.requires} to enter.`;
                    log.appendChild(msg);
                    log.scrollTop = log.scrollHeight;
                    return;
                }
            }
*/
