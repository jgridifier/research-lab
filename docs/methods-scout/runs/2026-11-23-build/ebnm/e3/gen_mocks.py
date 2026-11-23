"""Regenerate both SYNTHETIC Q2 mock ZBB datasets with seed 20261123 (only SEED overridden), then build
observable features with the 2026-11-13 prep.py logic. Output stays on the box (/workspace/scout/1123-build/)."""
import sys, runpy, importlib.util, pathlib
OUT = pathlib.Path('/workspace/scout/1123-build'); (OUT / 'data').mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('gen', '/workspace/q2-mock-zbb/generate_q2_mock_zbb.py'); G = importlib.util.module_from_spec(spec); sys.modules['gen'] = G; spec.loader.exec_module(G)
G.SEED = 20261123
G.main(['--out', str(OUT / 'mock')])
src = open('/workspace/rl-build-1123/docs/methods-scout/runs/2026-11-13/prep.py').read()
src = src.replace("SRC='/workspace/q2-mock-zbb/output/'", f"SRC='{OUT}/mock/'").replace("OUT='/workspace/scout/1113/data/'", f"OUT='{OUT}/data/'")
assert f"{OUT}/mock/" in src and f"{OUT}/data/" in src
exec(compile(src, 'prep_1113', 'exec'), {'__name__': '__main__'})
