"""Creator Atlas — Streamlit application entry point."""

from __future__ import annotations

import streamlit as st

from utils.config import APP_NAME, MAP_HEIGHT
from utils.data_loader import filter_creators, format_followers, load_creators
from utils.paths import CREATORS_CSV, DATA_PROCESSED_DIR, ensure_data_dirs
from utils.ui import inject_global_styles, render_hero, render_sidebar, render_status_metrics

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
    """Check whether processed map artifacts are present."""
    from utils.paths import EMBEDDINGS_PARQUET

    expected = (
        EMBEDDINGS_PARQUET,
        DATA_PROCESSED_DIR / "map_coords.parquet",
    )
    return all(path.exists() for path in expected)


def embeddings_ready() -> bool:
    from utils.paths import EMBEDDINGS_PARQUET

    return EMBEDDINGS_PARQUET.exists()


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

    if embeddings_ready():
        st.success("Embeddings are ready. UMAP map coordinates are the next step.")
    else:
        st.info("Run `python scripts/build_embeddings.py` to generate embeddings.")

    st.markdown("---")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Creator map")
        st.markdown(
            f"""
            <div class="placeholder-map">
                <div>
                    <p style="font-size: 1.25rem; color: #E6EDF3; margin-bottom: 0.5rem;">
                        Interactive map coming soon
                    </p>
                    <p style="font-size: 0.95rem;">
                        Embeddings and UMAP coordinates will power a Plotly scatter
                        plot here. Browse creators below while the AI pipeline is built.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Reserved plot height: {MAP_HEIGHT}px")

        st.subheader("Browse creators")
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
            selected_username = st.selectbox(
                "Select a creator",
                options=options,
                format_func=lambda u: labels[u],
            )
            selected_row = filtered.loc[filtered["username"] == selected_username].iloc[0]
            render_creator_detail(selected_row.to_dict())

        st.divider()
        st.subheader("Similar creators")
        st.caption("Top neighbors will appear here after the embedding pipeline runs.")


if __name__ == "__main__":
    main()
