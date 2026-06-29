"""Creator Atlas — immersive full-viewport exploration."""

from __future__ import annotations

import streamlit as st

from utils.config import NEIGHBOR_COUNT, ZOOM_STEP
from utils.data_loader import format_followers, load_creators, load_map_data
from utils.embeddings import load_embeddings_parquet
from utils.paths import CREATORS_CSV, EMBEDDINGS_PARQUET, MAP_COORDS_PARQUET, ensure_data_dirs
from utils.search import find_neighbors, format_similarity, semantic_search
from utils.ui import (
    inject_global_styles,
    render_atlas_background,
    render_explore_hint,
    render_panel_header,
    render_similar_chip,
    render_watermark,
)
from utils.viz import (
    LOD_TIER_DOTS,
    LOD_TIER_LABELS,
    LOD_TIER_REGIONS,
    build_creator_map_figure,
    compute_map_bounds,
    compute_zoom_factor,
    count_plotted_creators,
    infer_lod_tier,
    username_from_map_selection,
    zoom_ranges,
)

PLOT_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": False,
    "responsive": True,
}

st.set_page_config(
    page_title="Creator Atlas",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def map_coords_ready() -> bool:
    return MAP_COORDS_PARQUET.exists()


def embeddings_ready() -> bool:
    return EMBEDDINGS_PARQUET.exists()


@st.cache_resource(show_spinner=False)
def get_embedding_model():
    from utils.embeddings import load_embedding_model

    return load_embedding_model()


def _embeddings_mtime() -> float:
    return EMBEDDINGS_PARQUET.stat().st_mtime if EMBEDDINGS_PARQUET.exists() else 0.0


@st.cache_data(show_spinner=False)
def load_embeddings(_mtime: float):
    return load_embeddings_parquet(EMBEDDINGS_PARQUET)


def init_session_state() -> None:
    defaults = {
        "selected_username": None,
        "search_open": False,
        "semantic_query": "",
        "map_zoom_factor": 1.0,
        "map_center_x": None,
        "map_center_y": None,
        "focus_creator": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _tier_label(tier: int) -> str:
    if tier == LOD_TIER_REGIONS:
        return "Regions"
    if tier == LOD_TIER_DOTS:
        return "Creators"
    return "Names"


def _ensure_map_view(map_data, bounds: dict[str, list[float]]) -> tuple[tuple[float, float], tuple[float, float], int]:
    """Resolve zoom center, ranges, and LOD tier from session state."""
    focus = st.session_state.get("focus_creator")
    if focus and focus in map_data["username"].values:
        row = map_data[map_data["username"] == focus].iloc[0]
        st.session_state.map_center_x = float(row["x"])
        st.session_state.map_center_y = float(row["y"])
        st.session_state.map_zoom_factor = max(float(st.session_state.map_zoom_factor), 4.0)
        st.session_state.focus_creator = None

    center_x = st.session_state.map_center_x
    center_y = st.session_state.map_center_y
    if center_x is None or center_y is None:
        center_x = (bounds["x"][0] + bounds["x"][1]) / 2
        center_y = (bounds["y"][0] + bounds["y"][1]) / 2
        st.session_state.map_center_x = center_x
        st.session_state.map_center_y = center_y

    x_range, y_range = zoom_ranges(
        bounds,
        zoom_factor=float(st.session_state.map_zoom_factor),
        center_x=center_x,
        center_y=center_y,
    )
    tier = infer_lod_tier(compute_zoom_factor(bounds, x_range, y_range))
    return x_range, y_range, tier


def render_zoom_controls() -> None:
    st.markdown('<div class="atlas-zoom-controls">', unsafe_allow_html=True)
    if st.button("+", key="map_zoom_in", help="Zoom in"):
        st.session_state.map_zoom_factor = min(float(st.session_state.map_zoom_factor) * ZOOM_STEP, 12.0)
        st.rerun()
    tier = infer_lod_tier(float(st.session_state.map_zoom_factor))
    st.markdown(f'<div class="atlas-zoom-tier">{_tier_label(tier)}</div>', unsafe_allow_html=True)
    if st.button("−", key="map_zoom_out", help="Zoom out"):
        st.session_state.map_zoom_factor = max(float(st.session_state.map_zoom_factor) / ZOOM_STEP, 1.0)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def close_panel() -> None:
    st.session_state.selected_username = None


def render_floating_panel(creators_lookup: dict[str, dict]) -> None:
    username = st.session_state.selected_username
    if not username or username not in creators_lookup:
        return

    row = creators_lookup[username]

    with st.container(border=True):
        st.markdown('<div class="atlas-panel-marker"></div>', unsafe_allow_html=True)

        close_col, _ = st.columns([1, 5])
        with close_col:
            st.markdown('<div class="panel-close">', unsafe_allow_html=True)
            if st.button("×", key="close_panel", help="Close"):
                close_panel()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        render_panel_header(row["display_name"], row["username"], row["category"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Followers", format_followers(row.get("followers")))
        c2.metric("Likes", format_followers(row.get("avg_likes")))
        c3.metric("Views", format_followers(row.get("avg_views")))

        if row.get("bio"):
            st.write(row["bio"])

        st.link_button("Open profile →", row["profile_url"], use_container_width=True)

        if embeddings_ready():
            try:
                embeddings_df = load_embeddings(_embeddings_mtime())
                neighbors = find_neighbors(username, embeddings_df, k=NEIGHBOR_COUNT)
                if not neighbors.empty:
                    st.markdown('<p class="panel-section">Nearby creators</p>', unsafe_allow_html=True)
                    for _, match in neighbors.iterrows():
                        match_user = str(match["username"])
                        render_similar_chip(str(match["display_name"]), format_similarity(match["similarity"]))
                        if st.button(
                            f"View {match['display_name']}",
                            key=f"nav_{match_user}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_username = match_user
                            st.session_state.focus_creator = match_user
                            st.rerun()
            except FileNotFoundError:
                pass


def render_search_overlay(creators_lookup: dict[str, dict]) -> None:
    st.markdown('<div class="atlas-search-btn">', unsafe_allow_html=True)
    if st.button("⌕", key="search_toggle", help="Semantic search"):
        st.session_state.search_open = not st.session_state.search_open
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.search_open:
        return

    with st.container(border=True):
        st.markdown('<div class="atlas-search-marker"></div>', unsafe_allow_html=True)
        query = st.text_input(
            "Search",
            value=st.session_state.semantic_query,
            placeholder="Describe a creator… finance, comedy, beauty",
            label_visibility="collapsed",
        )
        st.session_state.semantic_query = query

        if query.strip() and embeddings_ready():
            try:
                embeddings_df = load_embeddings(_embeddings_mtime())
                matches = semantic_search(query, embeddings_df, model=get_embedding_model(), k=5)
                for _, match in matches.iterrows():
                    match_user = str(match["username"])
                    render_similar_chip(
                        str(match["display_name"]),
                        format_similarity(match["similarity"]),
                    )
                    if st.button(f"Go to {match['display_name']}", key=f"sem_{match_user}"):
                        st.session_state.selected_username = match_user
                        st.session_state.focus_creator = match_user
                        st.session_state.search_open = False
                        st.rerun()
            except FileNotFoundError:
                pass


def main() -> None:
    ensure_data_dirs()
    inject_global_styles()
    render_atlas_background()
    render_watermark()
    render_explore_hint()
    init_session_state()

    if not CREATORS_CSV.exists():
        st.error("Dataset missing. Run the collection script first.")
        return

    try:
        creators = load_creators()
    except ValueError as exc:
        st.error(str(exc))
        return

    if not map_coords_ready():
        st.warning("Run `build_embeddings.py` then `build_map.py` to activate the atlas.")
        return

    creators_lookup = {row["username"]: row.to_dict() for _, row in creators.iterrows()}

    try:
        map_data = load_map_data()
        selected = st.session_state.get("selected_username")
        bounds = compute_map_bounds(map_data)
        x_range, y_range, lod_tier = _ensure_map_view(map_data, bounds)

        fig, trace_frames, clickable_curves, lod_tier = build_creator_map_figure(
            map_data,
            selected_username=selected,
            lod_tier=lod_tier,
            x_range=x_range,
            y_range=y_range,
            bounds=bounds,
        )
        plotted_points = count_plotted_creators(trace_frames)

        render_zoom_controls()

        event = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="creator_map",
            config=PLOT_CONFIG,
        )

        clicked = username_from_map_selection(event, trace_frames, clickable_curves)
        if clicked:
            st.session_state.selected_username = clicked
            st.session_state.map_center_x = float(
                map_data[map_data["username"] == clicked]["x"].iloc[0]
            )
            st.session_state.map_center_y = float(
                map_data[map_data["username"] == clicked]["y"].iloc[0]
            )
            if lod_tier < LOD_TIER_LABELS:
                st.session_state.map_zoom_factor = max(float(st.session_state.map_zoom_factor), 4.0)
            selected = clicked

        selected_label = selected if selected else "None"
        st.markdown(
            f'<div class="atlas-debug">'
            f"Creators loaded: <b>{len(map_data)}</b> · "
            f"Plotted points: <b>{plotted_points}</b> · "
            f"View: <b>{_tier_label(lod_tier)}</b> · "
            f"Selected: <b>{selected_label}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    except FileNotFoundError as exc:
        st.error(str(exc))

    # ── Overlays (only after interaction) ──
    render_floating_panel(creators_lookup)
    render_search_overlay(creators_lookup)


if __name__ == "__main__":
    main()
