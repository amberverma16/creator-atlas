# Creator Atlas

An interactive map of social media creators powered by AI embeddings and dimensionality reduction. Search for a creator and explore where they sit in the broader creator landscape — alongside the people most similar to them.

Built as a standalone weekend project to demonstrate machine learning, semantic search, and data visualization.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

Creator Atlas turns creator profiles (bios, platforms, tags) into vector embeddings, reduces them to 2D coordinates with UMAP, and renders an explorable map. Proximity on the map reflects **semantic similarity**, not geography.

```
Raw profiles → Embeddings → UMAP (2D) → Interactive Plotly map
```

> **Status:** Milestone 0 complete — project scaffold and Streamlit shell. AI pipeline and map visualization arrive in upcoming milestones.

---

## Tech stack

| Layer | Tools |
|-------|-------|
| App | [Streamlit](https://streamlit.io) |
| Visualization | [Plotly](https://plotly.com/python/) |
| Data | [Pandas](https://pandas.pydata.org), [PyArrow](https://arrow.apache.org/docs/python/) |
| Embeddings | sentence-transformers *(Milestone 2)* |
| Dimensionality reduction | UMAP *(Milestone 3)* |

---

## Project structure

```
creator-atlas/
├── app.py                  # Streamlit entry point
├── requirements.txt
├── .env.example            # Optional API keys (OpenAI, etc.)
├── .streamlit/
│   └── config.toml         # Theme and server settings
├── assets/                 # Static assets (images, icons)
├── data/
│   ├── raw/                # Source creator CSV (committed sample)
│   └── processed/          # Generated parquet artifacts (gitignored)
├── utils/
│   ├── config.py           # App metadata and constants
│   ├── paths.py            # Filesystem paths
│   └── ui.py               # Shared Streamlit UI components
└── tests/
```

---

## Quick start

### 1. Clone and enter the repo

```bash
git clone https://github.com/amberverma16/creator-atlas.git
cd creator-atlas
```

### 2. Create a virtual environment

Requires **Python 3.11 or 3.12** (PyArrow wheels are not yet available for 3.14).

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Development

Run the test suite:

```bash
pytest
```

Optional environment variables (see `.env.example`):

```bash
cp .env.example .env
```

---

## Deployment

This project is structured for [Streamlit Community Cloud](https://streamlit.io/cloud):

| Setting | Value |
|---------|-------|
| Main file | `app.py` |
| Python version | 3.12 (see `.python-version`) |
| Dependencies | `requirements.txt` |

Push to GitHub and connect the repo in Streamlit Cloud — no extra configuration required.

---

## Roadmap

| Milestone | Description | Status |
|-----------|-------------|--------|
| 0 | Project scaffold & Streamlit shell | ✅ |
| 1 | Sample dataset & data loader | ⬜ |
| 2 | Embedding pipeline | ⬜ |
| 3 | UMAP map coordinates | ⬜ |
| 4 | Search & neighbor lookup | ⬜ |
| 5 | Interactive Plotly map | ⬜ |
| 6 | Polish & showcase README | ⬜ |

---

## License

MIT — see [LICENSE](LICENSE).
