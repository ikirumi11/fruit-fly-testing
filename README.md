# Fruit Fly Brain 3D

This repository contains the raw brain data plus a browser-based 3D viewer.

## Files

- `brain_raw.txt` — original raw data already in the repository.
- `index.html` — 3D browser viewer.
- `prepare_brain.py` — converts an NPZ, or a text dump containing an NPZ as JSON/base64/hex, into `brain.json`.
- `brain.json` — generated browser data, when conversion succeeds.

## Run

1. Install Python and NumPy.
2. Run `python prepare_brain.py`.
3. Serve the folder with a local web server, for example `python -m http.server 8000`.
4. Open `http://localhost:8000/`.

The viewer is deliberately conservative: it only displays coordinates and connections that are actually present in the source. It does not invent missing neural data.

If `brain_raw.txt` is a text representation that uses a different serialization than JSON/base64/hex, the raw file itself is preserved and the converter reports the exact unsupported format instead of silently producing fake brain data.
