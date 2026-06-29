"""Immersive atlas UI — full-viewport exploration."""

from __future__ import annotations

import streamlit as st

from utils.config import APP_NAME


def render_atlas_background() -> None:
    """Cartographic purple gradient with contour lines and particles."""
    st.markdown(
        """
        <div class="atlas-bg" aria-hidden="true">
            <div class="atlas-nebula atlas-nebula-1"></div>
            <div class="atlas-nebula atlas-nebula-2"></div>
            <div class="atlas-contours"></div>
            <div class="atlas-grid"></div>
            <canvas class="atlas-particles" id="atlas-particles"></canvas>
        </div>
        <script>
        (function () {
            const c = document.getElementById("atlas-particles");
            if (!c || c.dataset.ready) return;
            c.dataset.ready = "1";
            const ctx = c.getContext("2d");
            let w, h, pts;
            function resize() {
                w = c.width = innerWidth;
                h = c.height = innerHeight;
                pts = Array.from({length: 70}, () => ({
                    x: Math.random()*w, y: Math.random()*h,
                    r: Math.random()*1.2+0.2,
                    a: Math.random()*0.35+0.08,
                    vx: (Math.random()-0.5)*0.05,
                    vy: (Math.random()-0.5)*0.05,
                }));
            }
            function tick() {
                ctx.clearRect(0,0,w,h);
                for (const p of pts) {
                    p.x += p.vx; p.y += p.vy;
                    if (p.x<0)p.x=w; if (p.x>w)p.x=0;
                    if (p.y<0)p.y=h; if (p.y>h)p.y=0;
                    ctx.beginPath();
                    ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
                    ctx.fillStyle = `rgba(220,200,255,${p.a})`;
                    ctx.fill();
                }
                requestAnimationFrame(tick);
            }
            resize(); addEventListener("resize", resize); tick();
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


def inject_global_styles() -> None:
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --purple-deep: #4c1d95;
                --purple-mid: #6d28d9;
                --purple-soft: #7c3aed;
                --text: #f5f0ff;
                --muted: rgba(221, 214, 254, 0.65);
                --glass: rgba(76, 29, 149, 0.35);
                --glass-border: rgba(196, 181, 253, 0.28);
            }

            html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
                background: linear-gradient(160deg, #5b21b6 0%, #6d28d9 40%, #4c1d95 100%) !important;
                font-family: "Inter", -apple-system, sans-serif !important;
                color: var(--text);
            }

            /* Hide chrome */
            #MainMenu, footer, header[data-testid="stHeader"],
            [data-testid="stSidebar"], [data-testid="collapsedControl"] {
                display: none !important;
            }

            .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }

            /* Background layers */
            .atlas-bg { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
            .atlas-nebula {
                position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.45;
                animation: drift 28s ease-in-out infinite alternate;
            }
            .atlas-nebula-1 {
                width: 60vw; height: 60vw; top: -20%; left: -15%;
                background: radial-gradient(circle, rgba(167,139,250,0.5), transparent 70%);
            }
            .atlas-nebula-2 {
                width: 50vw; height: 50vw; bottom: -20%; right: -10%;
                background: radial-gradient(circle, rgba(99,102,241,0.35), transparent 70%);
                animation-delay: -10s;
            }
            .atlas-contours {
                position: absolute; inset: 0; opacity: 0.12;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='600'%3E%3Cpath d='M0 300 Q200 200 400 300 T800 300' fill='none' stroke='%23e9d5ff' stroke-width='1'/%3E%3Cpath d='M0 400 Q250 350 500 420 T800 380' fill='none' stroke='%23e9d5ff' stroke-width='0.8'/%3E%3Cpath d='M0 200 Q300 280 600 180 T800 220' fill='none' stroke='%23e9d5ff' stroke-width='0.8'/%3E%3C/svg%3E");
                background-size: cover;
            }
            .atlas-grid {
                position: absolute; inset: 0;
                background-image:
                    linear-gradient(rgba(233,213,255,0.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(233,213,255,0.05) 1px, transparent 1px);
                background-size: 80px 80px;
                mask-image: radial-gradient(ellipse 90% 80% at 50% 50%, black 10%, transparent 80%);
            }
            .atlas-particles { position: absolute; inset: 0; width: 100%; height: 100%; }
            @keyframes drift {
                from { transform: translate(0,0) scale(1); }
                to   { transform: translate(2%,3%) scale(1.05); }
            }

            /* Full-viewport Plotly map */
            [data-testid="stPlotlyChart"] {
                position: relative;
                z-index: 2;
                pointer-events: auto !important;
                min-height: calc(100vh - 6rem);
            }
            [data-testid="stPlotlyChart"] iframe,
            [data-testid="stPlotlyChart"] .js-plotly-plot,
            [data-testid="stPlotlyChart"] > div {
                pointer-events: auto !important;
                height: calc(100vh - 6rem) !important;
                min-height: calc(100vh - 6rem) !important;
            }
            .atlas-debug {
                position: relative;
                z-index: 3;
                pointer-events: auto !important;
                margin: 0.5rem 1rem 0;
                padding: 0.5rem 0.75rem;
                font-size: 0.8rem;
                color: rgba(221, 214, 254, 0.85);
                background: rgba(76, 29, 149, 0.45);
                border: 1px solid rgba(196, 181, 253, 0.25);
                border-radius: 8px;
                font-family: "Inter", sans-serif;
            }
            .main .block-container {
                pointer-events: none;
            }
            .main .block-container [data-testid="stPlotlyChart"],
            .main .block-container [data-testid="stVerticalBlockBorderWrapper"],
            .main .block-container .atlas-search-btn,
            .main .block-container .atlas-zoom-controls,
            .main .block-container .atlas-debug,
            .main .block-container [data-testid="stButton"],
            .main .block-container [data-testid="stTextInput"],
            .main .block-container [data-testid="stLinkButton"],
            .main .block-container [data-testid="stMetric"] {
                pointer-events: auto !important;
            }

            .atlas-hint-box {
                position: fixed;
                top: 1.25rem;
                right: 1.25rem;
                z-index: 10;
                pointer-events: none;
                font-size: 0.75rem;
                line-height: 1.5;
                color: rgba(221, 214, 254, 0.75);
                background: rgba(76, 29, 149, 0.35);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(196, 181, 253, 0.2);
                border-radius: 12px;
                padding: 0.65rem 0.85rem;
                max-width: 200px;
            }
            .atlas-hint-box strong {
                font-size: 0.68rem;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: rgba(245, 240, 255, 0.9);
            }

            /* Watermark */
            .atlas-watermark {
                position: fixed;
                top: 1.25rem;
                left: 1.5rem;
                z-index: 10;
                pointer-events: none;
                opacity: 0.55;
            }
            .atlas-watermark span {
                font-size: 0.8rem;
                font-weight: 500;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: var(--muted);
            }

            /* Floating glass panel (creator profile) */
            [data-testid="stVerticalBlockBorderWrapper"]:has(.atlas-panel-marker) {
                position: fixed !important;
                top: 1.25rem !important;
                right: 1.25rem !important;
                width: min(380px, calc(100vw - 2.5rem)) !important;
                max-height: calc(100vh - 2.5rem) !important;
                overflow-y: auto !important;
                z-index: 100 !important;
                background: var(--glass) !important;
                backdrop-filter: blur(24px) saturate(1.4) !important;
                -webkit-backdrop-filter: blur(24px) saturate(1.4) !important;
                border: 1px solid var(--glass-border) !important;
                border-radius: 20px !important;
                box-shadow: 0 16px 48px rgba(0,0,0,0.25), 0 0 60px rgba(124,58,237,0.15) !important;
                padding: 1.25rem 1.35rem !important;
                animation: panel-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) !important;
            }
            @keyframes panel-in {
                from { opacity: 0; transform: translateY(12px) scale(0.97); }
                to   { opacity: 1; transform: translateY(0) scale(1); }
            }

            /* Hidden search — reveals on toggle */
            [data-testid="stVerticalBlockBorderWrapper"]:has(.atlas-search-marker) {
                position: fixed !important;
                bottom: 1.25rem !important;
                left: 50% !important;
                transform: translateX(-50%) !important;
                width: min(480px, calc(100vw - 2rem)) !important;
                z-index: 50 !important;
                background: var(--glass) !important;
                backdrop-filter: blur(20px) !important;
                border: 1px solid var(--glass-border) !important;
                border-radius: 16px !important;
                padding: 0.75rem 1rem !important;
                animation: panel-in 0.35s ease !important;
            }

            .atlas-search-btn {
                position: fixed;
                bottom: 1.25rem;
                left: 1.25rem;
                z-index: 50;
            }
            .atlas-search-btn button {
                width: 44px !important;
                height: 44px !important;
                border-radius: 50% !important;
                background: var(--glass) !important;
                backdrop-filter: blur(12px) !important;
                border: 1px solid var(--glass-border) !important;
                color: var(--muted) !important;
                font-size: 1.1rem !important;
                opacity: 0.5;
                transition: opacity 0.2s, box-shadow 0.2s !important;
            }
            .atlas-search-btn button:hover {
                opacity: 1 !important;
                box-shadow: 0 0 24px rgba(167,139,250,0.3) !important;
            }

            .atlas-zoom-controls {
                position: fixed;
                bottom: 5.5rem;
                right: 1.25rem;
                z-index: 12;
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
            }
            .atlas-zoom-controls button {
                width: 2.25rem !important;
                height: 2.25rem !important;
                min-height: 2.25rem !important;
                padding: 0 !important;
                border-radius: 10px !important;
                background: rgba(76, 29, 149, 0.55) !important;
                border: 1px solid rgba(196, 181, 253, 0.35) !important;
                color: rgba(245, 240, 255, 0.95) !important;
                font-size: 1.1rem !important;
                line-height: 1 !important;
                backdrop-filter: blur(12px);
            }
            .atlas-zoom-controls button:hover {
                background: rgba(109, 40, 217, 0.65) !important;
                border-color: rgba(196, 181, 253, 0.55) !important;
            }
            .atlas-zoom-tier {
                text-align: center;
                font-size: 0.62rem;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                color: rgba(221, 214, 254, 0.65);
                padding: 0.15rem 0;
            }

            .panel-close button {
                background: transparent !important;
                border: none !important;
                color: var(--muted) !important;
                font-size: 1.25rem !important;
                padding: 0 !important;
                min-height: 0 !important;
                box-shadow: none !important;
            }
            .panel-close button:hover { color: var(--text) !important; transform: none !important; }

            .panel-name {
                font-size: 1.35rem;
                font-weight: 600;
                letter-spacing: -0.02em;
                margin: 0 0 0.15rem;
                color: var(--text);
            }
            .panel-handle {
                font-size: 0.85rem;
                color: var(--muted);
                margin-bottom: 0.75rem;
            }
            .panel-category {
                display: inline-block;
                font-size: 0.72rem;
                font-weight: 500;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: rgba(196,181,253,0.9);
                background: rgba(167,139,250,0.15);
                border: 1px solid rgba(167,139,250,0.25);
                border-radius: 999px;
                padding: 0.2rem 0.65rem;
                margin-bottom: 1rem;
            }
            .panel-bio {
                font-size: 0.88rem;
                line-height: 1.55;
                color: rgba(245,240,255,0.85);
                margin-bottom: 1rem;
            }
            .panel-section {
                font-size: 0.7rem;
                font-weight: 500;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--muted);
                margin: 1rem 0 0.5rem;
            }
            .similar-chip {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.55rem 0.7rem;
                margin: 0.3rem 0;
                border-radius: 10px;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(196,181,253,0.12);
                transition: background 0.2s, border-color 0.2s;
            }
            .similar-chip:hover {
                background: rgba(167,139,250,0.12);
                border-color: rgba(196,181,253,0.28);
            }
            .similar-chip-name { font-size: 0.85rem; font-weight: 500; }
            .similar-chip-score { font-size: 0.75rem; color: rgba(196,181,253,0.85); }

            [data-testid="stMetric"] {
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid rgba(196,181,253,0.1) !important;
                border-radius: 10px !important;
                padding: 0.4rem 0.6rem !important;
            }
            [data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.68rem !important; }
            [data-testid="stMetricValue"] { color: var(--text) !important; font-size: 0.95rem !important; }

            [data-testid="stTextInput"] input {
                background: rgba(255,255,255,0.07) !important;
                border: 1px solid var(--glass-border) !important;
                border-radius: 10px !important;
                color: var(--text) !important;
            }
            [data-testid="stLinkButton"] a {
                background: rgba(167,139,250,0.25) !important;
                border: 1px solid rgba(196,181,253,0.35) !important;
                border-radius: 10px !important;
                font-size: 0.85rem !important;
            }
            [data-testid="stAlert"], [data-testid="stNotification"] {
                position: fixed !important;
                top: 1rem !important;
                left: 50% !important;
                transform: translateX(-50%) !important;
                z-index: 200 !important;
                width: auto !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_explore_hint() -> None:
    st.markdown(
        """
        <div class="atlas-hint-box">
            <strong>How to explore</strong><br>
            +/− to zoom in · Drag to pan · Click a creator for details
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_watermark() -> None:
    st.markdown(
        f'<div class="atlas-watermark"><span>{APP_NAME}</span></div>',
        unsafe_allow_html=True,
    )


def render_panel_header(display_name: str, username: str, category: str) -> None:
    st.markdown(f'<p class="panel-name">{display_name}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="panel-handle">@{username}</p>', unsafe_allow_html=True)
    st.markdown(f'<span class="panel-category">{category}</span>', unsafe_allow_html=True)


def render_similar_chip(display_name: str, score: str) -> None:
    st.markdown(
        f"""
        <div class="similar-chip">
            <span class="similar-chip-name">{display_name}</span>
            <span class="similar-chip-score">{score}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
