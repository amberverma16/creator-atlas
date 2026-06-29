"""Tests for atlas map payload preparation."""

import pandas as pd

from utils.atlas_map_component import prepare_map_payload


def test_prepare_map_payload_structure() -> None:
    df = pd.DataFrame(
        [
            {"username": "a", "display_name": "A", "category": "Comedy", "x": 1.0, "y": 2.0, "followers": 10000},
            {"username": "b", "display_name": "B", "category": "Dance", "x": 3.0, "y": 4.0, "followers": 20000},
        ]
    )
    payload = prepare_map_payload(df)
    assert len(payload["creators"]) == 2
    assert len(payload["categories"]) == 2
    assert "x" in payload["bounds"] and "y" in payload["bounds"]


def test_prepare_map_payload_empty() -> None:
    payload = prepare_map_payload(pd.DataFrame())
    assert payload["creators"] == []
