"""Step-2 speed/memory: streamed Rust core on SYNTHETIC random walks (seed 20261123), height 300.
Peak RSS from wait4() rusage (ru_maxrss of the child, KiB). Median of 3 for 10k; one run for 50k."""
import subprocess, json, os, resource, statistics
B = os.path.dirname(os.path.abspath(__file__)) + "/core/target/release/dl"
def run(n, w=1000, h=300, chunk=10000):
    p = subprocess.Popen([B, "--bench", str(n), str(w), str(h), str(chunk)], stdout=subprocess.PIPE, text=True)
    out = p.stdout.read(); _, status, ru = os.wait4(p.pid, 0)
    r = json.loads(out); r["peak_rss_MB"] = ru.ru_maxrss / 1024; return r
r10 = [run(10000) for _ in range(3)]; r50 = run(50000)
res = {"data": "SYNTHETIC random walks (xorshift, seed 20261123)", "threads": r10[0]["threads"], "host": "box, 8 vCPU, shared with other jobs",
  "n10000_w1000": {"runs": r10, "median_density_s": statistics.median(r["density_s"] for r in r10), "median_total_s": statistics.median(r["total_s"] for r in r10)},
  "n50000_w1000": r50,
  "reference_11_13": {"rust_reference_10k_s": 0.50, "numpy_port_10k_s": 62, "reference_50k": "killed at the 15.6 GB memory limit"}}
res["accept"] = "10,000 x 1,000 in <= 0.5 s; 50,000 series finish with peak RSS < 2 GB"
res["pass"] = res["n10000_w1000"]["median_total_s"] <= 0.5 and r50["peak_rss_MB"] < 2048
json.dump(res, open("bench.json", "w"), indent=1); print(json.dumps(res, indent=1))
