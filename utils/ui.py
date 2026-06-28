"""Reusable Streamlit UI helpers."""

from __future__ import annotations

import streamlit as st

from utils.config import APP_NAME, APP_TAGLINE, APP_VERSION


def inject_global_styles() -> None:
    """Apply shared CSS for a polished, deployment-ready layout."""
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1100px;
            }
            .hero-title {
                font-size: 2.75rem;
                font-weight: 700;
                letter-spacing: -0.03em;
                line-height: 1.1;
                margin-bottom: 0.5rem;
            }
            .hero-subtitle {
                font-size: 1.125rem;
                color: #8B949E;
                margin-bottom: 1.75rem;
                max-width: 42rem;
            }
            .metric-card {
                background: #161B22;
                border: 1px solid #30363D;
                border-radius: 12px;
                padding: 1rem 1.25rem;
            }
            .placeholder-map {
                background: linear-gradient(145deg, #161B22 0%, #0D1117 100%);
                border: 1px dashed #30363D;
                border-radius: 16px;
                min-height: 420px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                color: #8B949E;
                padding: 2rem;
            }
            div[data-testid="stSidebar"] {
                background-color: #0D1117;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(*, creator_count: int = 0, category_count: int = 0) -> None:
    """Render the application sidebar."""
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption(f"v{APP_VERSION}")
        st.divider()

        st.markdown("**About**")
        st.markdown(
            "Creator Atlas maps social media creators in a 2D space where "
            "proximity reflects semantic similarity — not geography."
        )

        if creator_count:
            st.caption(f"Dataset: **{creator_count}** creators · **{category_count}** categories")

        st.divider()
        st.markdown("**Roadmap**")
        st.markdown(
            """
            - [x] Project scaffold
            - [x] Creator dataset
            - [x] Embedding pipeline
            - [x] UMAP coordinates
            - [ ] Search & neighbors
            - [x] Interactive map
            """
        )

        st.divider()
        st.caption(APP_TAGLINE)


def render_hero() -> None:
    """Render the page hero section."""
    st.markdown(
        f'<p class="hero-title">{APP_NAME}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="hero-subtitle">{APP_TAGLINE}</p>',
        unsafe_allow_html=True,
    )


def render_status_metrics(
    creator_count: int,
    category_count: int,
    processed_ready: bool,
) -> None:
    """Show high-level project status metrics."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Creators loaded", creator_count)

    with col2:
        st.metric("Categories", category_count)

    with col3:
        st.metric(
            "Map data",
            "Ready" if processed_ready else "Pending",
        )
