// pimperm: within-year permutation refits of a logit PIM (difference model), Newton per permutation, rayon over permutations.
// Post-hoc engineering extra for research-lab #63 (not the pre-registered numpy prototype). 2026-11-17.
// Input (stdin, whitespace): n k nperm seed nchk; then n lines: year y x1..xk (rows sorted by year).
// Output: nperm lines of beta; then nchk lines of permuted y (for parity checks).
use rayon::prelude::*;
use std::io::{self, Read, Write};
use std::time::Instant;

fn splitmix(s: &mut u64) -> u64 { *s = s.wrapping_add(0x9E3779B97F4A7C15); let mut z = *s;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9); z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB); z ^ (z >> 31) }

fn main() {
    let mut s = String::new(); io::stdin().read_to_string(&mut s).unwrap();
    let v: Vec<f64> = s.split_whitespace().map(|t| t.parse().unwrap()).collect();
    let (n, k, nperm, seed, nchk) = (v[0] as usize, v[1] as usize, v[2] as usize, v[3] as u64, v[4] as usize);
    let mut year = vec![0i64; n]; let mut y = vec![0f64; n]; let mut x = vec![0f64; n * k];
    for i in 0..n { let o = 5 + i * (2 + k); year[i] = v[o] as i64; y[i] = v[o + 1]; for j in 0..k { x[i * k + j] = v[o + 2 + j]; } }
    // blocks and pairs (same order as R combn within sorted years)
    let mut blocks: Vec<(usize, usize)> = vec![]; let mut st = 0;
    for i in 1..=n { if i == n || year[i] != year[st] { blocks.push((st, i)); st = i; } }
    let mut pi = vec![]; let mut pj = vec![];
    for &(a, b) in &blocks { for i in a..b { for j in i + 1..b { pi.push(i); pj.push(j); } } }
    let p = pi.len(); let mut z = vec![0f64; p * k];
    for q in 0..p { for j in 0..k { z[q * k + j] = x[pj[q] * k + j] - x[pi[q] * k + j]; } }
    let t0 = Instant::now();
    let res: Vec<(Vec<f64>, Vec<f64>)> = (0..nperm).into_par_iter().map(|r| {
        let mut rs = seed ^ ((r as u64 + 1).wrapping_mul(0xD1B54A32D192ED03));
        let mut yp = y.clone();
        for &(a, b) in &blocks { for i in (a + 1..b).rev() { let j = a + (splitmix(&mut rs) % ((i - a + 1) as u64)) as usize; yp.swap(i, j); } }
        let ii: Vec<f64> = (0..p).map(|q| { let (u, w) = (yp[pi[q]], yp[pj[q]]); if u < w { 1.0 } else if u == w { 0.5 } else { 0.0 } }).collect();
        let mut b = vec![0f64; k];
        for _ in 0..50 {
            let mut g = vec![0f64; k]; let mut h = vec![0f64; k * k];
            for q in 0..p { let zq = &z[q * k..q * k + k]; let e: f64 = zq.iter().zip(&b).map(|(a, c)| a * c).sum();
                let pr = 1.0 / (1.0 + (-e).exp()); let w = pr * (1.0 - pr); let rq = ii[q] - pr;
                for a in 0..k { g[a] += zq[a] * rq; for c in 0..k { h[a * k + c] += w * zq[a] * zq[c]; } } }
            let gmax = g.iter().fold(0f64, |m, t| m.max(t.abs()));
            // solve h d = g (Gaussian elimination, small k)
            let mut m = h.clone(); let mut d = g.clone();
            for c in 0..k { let piv = m[c * k + c]; for r2 in c + 1..k { let f = m[r2 * k + c] / piv; for cc in c..k { m[r2 * k + cc] -= f * m[c * k + cc]; } d[r2] -= f * d[c]; } }
            for c in (0..k).rev() { let mut sm = d[c]; for cc in c + 1..k { sm -= m[c * k + cc] * d[cc]; } d[c] = sm / m[c * k + c]; }
            for a in 0..k { b[a] += d[a]; }
            if gmax < 1e-10 { break; }
        }
        (b, if r < nchk { yp } else { vec![] })
    }).collect();
    let el = t0.elapsed().as_secs_f64();
    let mut out = io::BufWriter::new(io::stdout());
    for (b, _) in &res { writeln!(out, "{}", b.iter().map(|t| format!("{:.17e}", t)).collect::<Vec<_>>().join(" ")).unwrap(); }
    for (_, yp) in res.iter().take(nchk) { writeln!(out, "{}", yp.iter().map(|t| format!("{:.17e}", t)).collect::<Vec<_>>().join(" ")).unwrap(); }
    eprintln!("pairs {} perms {} seconds {:.4} threads {}", p, nperm, el, rayon::current_num_threads());
}
