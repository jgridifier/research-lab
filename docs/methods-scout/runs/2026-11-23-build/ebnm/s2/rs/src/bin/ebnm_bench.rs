// ebnm_bench <xs.csv> <scale.txt|-> <grid_mult> <out.json> <boot_reps> <seed>
// xs.csv: two columns x,s (SYNTHETIC mock). scale.txt: explicit grid (else computed from grid_mult).
use ebnm_core::*; use rayon::prelude::*; use std::io::Write; use std::time::Instant;
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let txt = std::fs::read_to_string(&a[1]).unwrap();
    let (mut x, mut s) = (vec![], vec![]);
    for line in txt.lines() { let v: Vec<f64> = line.split(',').map(|t| t.trim().parse().unwrap()).collect(); x.push(v[0]); s.push(v[1]); }
    let gm: f64 = a[3].parse().unwrap();
    let scale: Vec<f64> = if a[2] != "-" { std::fs::read_to_string(&a[2]).unwrap().split_whitespace().map(|t| t.parse().unwrap()).collect() } else { scale_grid(&x, &s, gm) };
    let fit = ash_fit(&x, &s, &scale);
    let mut ts = vec![];
    for _ in 0..200 { let t = Instant::now(); let g = scale_grid(&x, &s, gm); let f = ash_fit(&x, &s, if a[2] != "-" { &scale } else { &g }); std::hint::black_box(f.loglik); ts.push(t.elapsed().as_secs_f64()); }
    ts.sort_by(|p, q| p.partial_cmp(q).unwrap());
    let reps: usize = a[5].parse().unwrap(); let seed: u64 = a[6].parse().unwrap();
    let n = x.len();
    let t = Instant::now();
    let lls: Vec<f64> = (0..reps).into_par_iter().map(|r| {
        let mut st = seed ^ ((r as u64 + 1).wrapping_mul(0x9E3779B97F4A7C15));
        let mut nxt = || { st ^= st << 13; st ^= st >> 7; st ^= st << 17; st };
        let (mut xb, mut sb) = (Vec::with_capacity(n), Vec::with_capacity(n));
        for _ in 0..n { let i = (nxt() % n as u64) as usize; xb.push(x[i]); sb.push(s[i]); }
        let g = scale_grid(&xb, &sb, gm); ash_fit(&xb, &sb, &g).loglik
    }).collect();
    let boot_s = t.elapsed().as_secs_f64();
    let mut o = std::fs::File::create(&a[4]).unwrap();
    let js = |v: &[f64]| v.iter().map(|z| format!("{:e}", z)).collect::<Vec<_>>().join(",");
    write!(o, "{{\"loglik\":{:e},\"iters\":{},\"K\":{},\"fit_ms_median200\":{},\"boot_reps\":{},\"boot_s\":{},\"threads\":{},\"boot_ll_mean\":{},\"pi\":[{}],\"post_mean\":[{}],\"lfsr\":[{}]}}",
        fit.loglik, fit.iters, scale.len(), 1000.0 * ts[100], reps, boot_s, rayon::current_num_threads(), lls.iter().sum::<f64>() / reps as f64, js(&fit.pi), js(&fit.post_mean), js(&fit.lfsr)).unwrap();
}
