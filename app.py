"""Creator Atlas — Streamlit application entry point."""

from __future__ import annotations

import streamlit as st

from utils.config import APP_NAME
from utils.data_loader import filter_creators, format_followers, load_creators, load_map_data
from utils.paths import CREATORS_CSV, EMBEDDINGS_PARQUET, MAP_COORDS_PARQUET, ensure_data_dirs
from utils.ui import inject_global_styles, render_hero, render_sidebar, render_status_metrics
from utils.viz import build_creator_map_figure, username_from_map_selection

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

TABLE_COLUMNS = [
    "display_name",
    "username",
    "category",
    "followers",
    "avg_likes",
    "avg_views",
    "caption_count",
]


def processed_artifacts_exist() -> bool:
    return EMBEDDINGS_PARQUET.exists() and MAP_COORDS_PARQUET.exists()


def map_coords_ready() -> bool:
    return MAP_COORDS_PARQUET.exists()


def init_session_state(default_username: str | None) -> None:
    if "selected_username" not in st.session_state and default_username:
        st.session_state.selected_username = default_username


def render_creator_detail(row: dict) -> None:
    st.subheader(row["display_name"])
    st.caption(f"@{row['username']} · {row['category']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Followers", format_followers(row.get("followers")))
    col2.metric("Avg likes", format_followers(row.get("avg_likes")))
    col3.metric("Avg views", format_followers(row.get("avg_views")))

    if row.get("bio"):
        st.markdown("**Bio**")
        st.write(row["bio"])

    st.link_button("Open TikTok profile", row["profile_url"], use_container_width=True)

    captions = row.get("recent_captions_list") or []
    if captions:
        st.markdown("**Recent captions**")
        for caption in captions[:6]:
            st.markdown(f"- {caption}")

    hashtags = row.get("hashtags_list") or []
    if hashtags:
        st.markdown("**Hashtags**")
        st.write(", ".join(f"#{tag}" for tag in hashtags[:20]))


def render_dataset_table(df) -> None:
    display_df = df[TABLE_COLUMNS].copy()
    display_df["followers"] = display_df["followers"].map(format_followers)
    display_df["avg_likes"] = display_df["avg_likes"].map(format_followers)
    display_df["avg_views"] = display_df["avg_views"].map(format_followers)
    display_df = display_df.rename(
        columns={
            "display_name": "Name",
            "username": "Username",
            "category": "Category",
            "followers": "Followers",
            "avg_likes": "Avg likes",
            "avg_views": "Avg views",
            "caption_count": "Captions",
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_map_section(filtered) -> str | None:
    """Render the Plotly map and return a username selected via click, if any."""
    if filtered.empty:
        st.info("No creators match your filters.")
        return None

    selected_username = st.session_state.get("selected_username")
    if selected_username not in filtered["username"].values:
        selected_username = filtered.iloc[0]["username"]
        st.session_state.selected_username = selected_username

    fig, trace_frames = build_creator_map_figure(
        filtered,
        selected_username=selected_username,
    )
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="creator_map",
    )

    clicked_username = username_from_map_selection(event, trace_frames)
    if clicked_username:
        st.session_state.selected_username = clicked_username
        return clicked_username

    return None


def main() -> None:
    ensure_data_dirs()
    inject_global_styles()

    if not CREATORS_CSV.exists():
        render_sidebar()
        render_hero()
        st.error(
            f"No dataset found at `{CREATORS_CSV}`. "
            "Run `python scripts/collect_tiktok_creators.py` first."
        )
        return

    try:
        creators = load_creators()
    except ValueError as exc:
        render_sidebar()
        render_hero()
        st.error(str(exc))
        return

    category_count = creators["category"].nunique()
    render_sidebar(creator_count=len(creators), category_count=category_count)
    render_hero()
    render_status_metrics(len(creators), category_count, processed_artifacts_exist())

    if not map_coords_ready():
        st.warning(
            "Map coordinates are missing. Run `python scripts/build_embeddings.py` "
            "then `python scripts/build_map.py`."
        )

    st.markdown("---")

    search_query = st.text_input(
        "Search",
        placeholder="Name, username, bio, or category…",
    )
    all_categories = sorted(creators["category"].dropna().unique())
    selected_categories = st.multiselect(
        "Filter by category",
        options=all_categories,
        default=[],
        placeholder="All categories",
    )

    filtered = filter_creators(
        creators,
        query=search_query,
        categories=selected_categories or None,
    )
    init_session_state(filtered.iloc[0]["username"] if not filtered.empty else None)

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Creator map")
        if map_coords_ready():
            try:
                map_data = load_map_data()
                map_filtered = map_data[map_data["username"].isin(filtered["username"])].copy()
                render_map_section(map_filtered)
                st.caption("Click a dot to select a creator. Proximity reflects semantic similarity.")
            except FileNotFoundError as exc:
                st.error(str(exc))
        else:
            st.info("Generate map coordinates to see the interactive atlas.")

        st.subheader("Browse creators")
        st.caption(f"Showing **{len(filtered)}** of **{len(creators)}** creators")
        render_dataset_table(filtered)

    with right:
        st.subheader("Creator profile")
        if filtered.empty:
            st.info("No creators match your filters.")
        else:
            options = filtered["username"].tolist()
            labels = {
                row["username"]: f"{row['display_name']} (@{row['username']})"
                for _, row in filtered.iterrows()
            }
            current = st.session_state.get("selected_username", options[0])
            if current not in options:
                current = options[0]

            selected_username = st.selectbox(
                "Select a creator",
                options=options,
                index=options.index(current),
                format_func=lambda u: labels[u],
                key="creator_selectbox",
            )
            st.session_state.selected_username = selected_username
            selected_row = filtered.loc[filtered["username"] == selected_username].iloc[0]
            render_creator_detail(selected_row.to_dict())

        st.divider()
        st.subheader("Similar creators")
        st.caption("Top neighbors will appear here in Milestone 4 (semantic search).")


if __name__ == "__main__":
    main()
