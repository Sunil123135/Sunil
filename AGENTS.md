# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
A collection of **standalone data-science / ML Jupyter notebooks** (statistical
learning, ensemble methods, neural networks, recommendation systems). There is
no application server or build step — the "app" is the notebooks themselves, run
in Jupyter. Each notebook is independent.

### Running the notebooks (dev server)
From the repo root:

```
jupyter lab --no-browser --ip=0.0.0.0 --port=8888 --ServerApp.token="" --ServerApp.password=""
```

Then open `http://localhost:8888/lab`. To execute a notebook headlessly:
`jupyter nbconvert --to notebook --execute <file>.ipynb`.

### Non-obvious gotchas
- **PATH**: Python packages install to `~/.local/bin` (user site). It is added to
  `~/.bashrc`, so login shells find `jupyter`. If a non-login shell can't find it,
  use the module form instead: `python3 -m jupyterlab` / `python3 -m jupyter nbconvert`.
- **Notebooks won't all run top-to-bottom unmodified.** Many were authored on
  Google Colab against old library versions and use APIs that no longer exist on
  the modern stack (e.g. `from google.colab import drive`,
  `from sklearn.externals import joblib`, `from sklearn.externals.six import StringIO`,
  `from keras.utils.np_utils import to_categorical`). Several also read CSV/data
  files that are **not included** in the repo. Treat these notebooks as learning
  artifacts: run cells selectively and modernize imports as needed for the cells
  you care about. This is expected, not an environment problem.
- Dependencies are listed in `requirements.txt` and installed by the startup
  update script; reinstalling is idempotent.
