"""Convert the repository's raw brain data into the compact browser format.

Usage:
  python prepare_brain.py
  python prepare_brain.py path/to/brain.npz

The converter accepts an NPZ directly, or a text file containing JSON,
base64, or hexadecimal bytes for an NPZ. It intentionally does not invent
neuron coordinates when the source does not contain them.
"""
from __future__ import annotations
import base64, binascii, io, json, re, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "brain_raw.txt"
out_path = ROOT / "brain.json"

def clean_npz(z):
    keys = list(z.files)
    def pick(*names):
        for n in names:
            if n in z: return np.asarray(z[n])
        for k in keys:
            lk=k.lower()
            if any(n in lk for n in names): return np.asarray(z[k])
        return None
    nodes = pick("neurons","nodes","positions","coords","coordinates","xyz")
    edges = pick("edges","connections","connectivity","synapses")
    if nodes is None:
        raise ValueError(f"No neuron/node coordinate array found. NPZ arrays: {keys}")
    nodes = np.asarray(nodes)
    if nodes.ndim != 2 or nodes.shape[1] < 3:
        raise ValueError(f"Neuron coordinates must be Nx3 or wider; got {nodes.shape}")
    nodes = nodes[:, :3].astype(float)
    if edges is None:
        edges_out=[]
    else:
        edges=np.asarray(edges)
        if edges.ndim==2 and edges.shape[1]>=2:
            edges_out=edges[:, :2].astype(np.int64).tolist()
        else:
            edges_out=[]
    return {"neurons":nodes.tolist(),"edges":edges_out,"source_arrays":keys}

def load_npz_bytes(data):
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        return clean_npz(z)

def try_text(text):
    text=text.strip()
    try:
        obj=json.loads(text)
        if isinstance(obj,dict):
            if "neurons" in obj or "nodes" in obj:
                nodes=obj.get("neurons",obj.get("nodes")); edges=obj.get("edges",obj.get("connections",[]))
                return {"neurons":nodes,"edges":edges,"source":"json"}
            for key,val in obj.items():
                if isinstance(val,str):
                    try:return load_npz_bytes(base64.b64decode(val,validate=True))
                    except Exception:pass
    except Exception: pass
    # Search for a large base64 block. This handles text dumps containing one.
    compact=re.sub(r"\s+","",text)
    for candidate in (compact, re.findall(r"[A-Za-z0-9+/]{1000,}={0,2}",text)[0] if re.findall(r"[A-Za-z0-9+/]{1000,}={0,2}",text) else ""):
        try:
            b=base64.b64decode(candidate,validate=True)
            if b[:2]==b"PK": return load_npz_bytes(b)
        except Exception: pass
    # Search for a long hexadecimal NPZ byte dump.
    hx=re.sub(r"[^0-9a-fA-F]","",text)
    if len(hx)>2000 and len(hx)%2==0:
        try:
            b=binascii.unhexlify(hx)
            if b[:2]==b"PK": return load_npz_bytes(b)
        except Exception: pass
    raise ValueError("Could not identify JSON, base64 NPZ, or hexadecimal NPZ data in brain_raw.txt")

if raw_path.suffix.lower()==".npz":
    result=load_npz_bytes(raw_path.read_bytes())
else:
    result=try_text(raw_path.read_text(encoding="utf-8",errors="ignore"))

# Keep the browser payload manageable while preserving exact source values.
result["format"]="fruit-fly-browser-v1"
result["neuron_count"]=len(result["neurons"])
result["edge_count"]=len(result["edges"])
out_path.write_text(json.dumps(result,separators=(",",":")),encoding="utf-8")
print(f"Wrote {out_path} with {result['neuron_count']:,} neurons and {result['edge_count']:,} connections.")
