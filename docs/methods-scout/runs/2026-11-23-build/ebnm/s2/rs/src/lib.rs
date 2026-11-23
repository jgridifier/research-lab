//! ash EBNM fit (mode 0), same algorithm as sqp_np.py: L matrix, active-set SQP on
//! f(x) = -(1/n) sum_j log(L_j x) + sum x, closed-form posteriors and lfsr. Independent code (research prototype).

pub struct Fit { pub pi: Vec<f64>, pub loglik: f64, pub post_mean: Vec<f64>, pub post_sd: Vec<f64>, pub lfsr: Vec<f64>, pub iters: usize }

/// ebnm-style scale grid: sqrt(min_s2 * (m^(0..K-1) - 1)), m clamped to [min_mult, max_mult]
pub fn scale_grid(x: &[f64], s: &[f64], grid_mult: f64) -> Vec<f64> {
    let (min_k, max_k) = (3.0f64, 300.0f64);
    let max_x2 = x.iter().map(|v| v * v).fold(0.0, f64::max);
    let min_s = s.iter().cloned().fold(f64::INFINITY, f64::min);
    let min_s2 = min_s * min_s;
    let ratio = (max_x2 / min_s2).max(1.0);
    let max_mult = (ratio + 1.0).powf(1.0 / (min_k - 1.0)) + 1e-8;
    let min_mult = max_mult.powf((min_k - 1.0) / (max_k - 1.0)) - 1e-8;
    let m = grid_mult.max(min_mult).min(max_mult);
    let k = ((ratio + 1.0).ln() / m.ln()).ceil() as usize + 1;
    (0..k).map(|i| (min_s2 * (m.powi(i as i32) - 1.0)).sqrt()).collect()
}

fn solve_sym(a: &mut [f64], b: &mut [f64], k: usize) -> bool {
    // Cholesky in place (a is k x k row-major), then solve
    for j in 0..k {
        let mut d = a[j * k + j];
        for p in 0..j { d -= a[j * k + p] * a[j * k + p]; }
        if d <= 0.0 { return false; }
        let d = d.sqrt(); a[j * k + j] = d;
        for i in j + 1..k {
            let mut v = a[i * k + j];
            for p in 0..j { v -= a[i * k + p] * a[j * k + p]; }
            a[i * k + j] = v / d;
        }
    }
    for i in 0..k { let mut v = b[i]; for p in 0..i { v -= a[i * k + p] * b[p]; } b[i] = v / a[i * k + i]; }
    for i in (0..k).rev() { let mut v = b[i]; for p in i + 1..k { v -= a[p * k + i] * b[p]; } b[i] = v / a[i * k + i]; }
    true
}

fn sub_solve(h: &[f64], b: &[f64], p: &[bool], k: usize, z: &mut [f64]) {
    let idx: Vec<usize> = (0..k).filter(|&i| p[i]).collect();
    let m = idx.len();
    let mut a = vec![0.0; m * m]; let mut r = vec![0.0; m];
    for (ii, &i) in idx.iter().enumerate() { r[ii] = -b[i]; for (jj, &j) in idx.iter().enumerate() { a[ii * m + jj] = h[i * k + j]; } }
    solve_sym(&mut a, &mut r, m);
    for v in z.iter_mut() { *v = 0.0; }
    for (ii, &i) in idx.iter().enumerate() { z[i] = r[ii]; }
}

fn nnqp(h: &[f64], b: &[f64], x0: &[f64], k: usize) -> Vec<f64> {
    let mut p: Vec<bool> = x0.iter().map(|&v| v > 0.0).collect();
    let mut y = vec![0.0; k]; let mut z = vec![0.0; k];
    if p.iter().any(|&q| q) {
        sub_solve(h, b, &p, k, &mut z);
        if (0..k).all(|i| !p[i] || z[i] > 0.0) { y.copy_from_slice(&z); } else { p.iter_mut().for_each(|q| *q = false); }
    }
    for _ in 0..100 {
        let mut best = -f64::INFINITY; let mut bi = usize::MAX;
        for i in 0..k { if !p[i] { let mut w = -b[i]; for j in 0..k { w -= h[i * k + j] * y[j]; } if w > best { best = w; bi = i; } } }
        if bi == usize::MAX || best <= 1e-12 { break; }
        p[bi] = true;
        loop {
            sub_solve(h, b, &p, k, &mut z);
            if (0..k).all(|i| !p[i] || z[i] > 0.0) { y.copy_from_slice(&z); break; }
            let mut a = f64::INFINITY;
            for i in 0..k { if p[i] && z[i] <= 0.0 { a = a.min(y[i] / (y[i] - z[i])); } }
            for i in 0..k { y[i] += a * (z[i] - y[i]); if p[i] && y[i] <= 1e-15 { p[i] = false; y[i] = 0.0; } }
        }
    }
    y
}

pub fn mix_sqp(l: &[f64], n: usize, k: usize) -> (Vec<f64>, usize) {
    let mut x = vec![1.0 / k as f64; k];
    let f = |x: &[f64]| -> f64 { let mut acc = 0.0; for j in 0..n { let mut u = 0.0; for c in 0..k { u += l[j * k + c] * x[c]; } acc += u.ln(); } -acc / n as f64 + x.iter().sum::<f64>() };
    let mut fx = f(&x);
    let mut it = 0;
    let mut a_row = vec![0.0; k];
    while it < 200 {
        it += 1;
        let mut g = vec![0.0; k]; let mut h = vec![0.0; k * k];
        for j in 0..n {
            let row = &l[j * k..(j + 1) * k];
            let mut u = 0.0; for c in 0..k { u += row[c] * x[c]; }
            for c in 0..k { a_row[c] = row[c] / u; g[c] -= a_row[c]; }
            for c in 0..k { let ac = a_row[c]; if ac == 0.0 { continue; } for d in c..k { h[c * k + d] += ac * a_row[d]; } }
        }
        let inv = 1.0 / n as f64;
        for c in 0..k { g[c] = g[c] * inv + 1.0; for d in c..k { h[c * k + d] *= inv; h[d * k + c] = h[c * k + d]; } h[c * k + c] += 1e-10; }
        let mut gmax_sup = -f64::INFINITY; let mut gmin = f64::INFINITY;
        for c in 0..k { if x[c] > 0.0 { gmax_sup = gmax_sup.max(g[c]); } gmin = gmin.min(g[c]); }
        if gmax_sup - gmin < 1e-10 && gmin >= -1e-10 { break; }
        let mut b = vec![0.0; k];
        for c in 0..k { let mut v = g[c]; for d in 0..k { v -= h[c * k + d] * x[d]; } b[c] = v; }
        let y = nnqp(&h, &b, &x, k);
        let d: Vec<f64> = (0..k).map(|c| y[c] - x[c]).collect();
        let gd: f64 = (0..k).map(|c| g[c] * d[c]).sum();
        let mut a = 1.0; let mut xn = vec![0.0; k]; let mut fnew;
        loop {
            for c in 0..k { xn[c] = x[c] + a * d[c]; }
            fnew = f(&xn);
            if fnew <= fx + 0.01 * a * gd || a < 1e-10 { break; }
            a *= 0.5;
        }
        let step = d.iter().map(|v| (a * v).abs()).fold(0.0, f64::max);
        x.copy_from_slice(&xn); fx = fnew;
        if step < 1e-12 { break; }
    }
    let s: f64 = x.iter().map(|v| v.max(0.0)).sum();
    (x.iter().map(|v| v.max(0.0) / s).collect(), it)
}

pub fn ash_fit(x: &[f64], s: &[f64], scale: &[f64]) -> Fit {
    let n = x.len(); let k = scale.len();
    let mut l = vec![0.0; n * k]; let mut norms = vec![0.0; n];
    for j in 0..n {
        let mut mx = f64::NEG_INFINITY;
        for c in 0..k { let sig2 = s[j] * s[j] + scale[c] * scale[c]; let v = -0.5 * (sig2.ln() + x[j] * x[j] / sig2); l[j * k + c] = v; mx = mx.max(v); }
        norms[j] = mx; for c in 0..k { l[j * k + c] = (l[j * k + c] - mx).exp(); }
    }
    let (pi, iters) = mix_sqp(&l, n, k);
    let mut loglik = 0.0; let mut pm = vec![0.0; n]; let mut psd = vec![0.0; n]; let mut lfsr = vec![0.0; n];
    for j in 0..n {
        let row = &l[j * k..(j + 1) * k];
        let mut tot = 0.0; for c in 0..k { tot += row[c] * pi[c]; }
        loglik += tot.ln() + norms[j];
        let (mut m1, mut m2, mut ppos, mut pz) = (0.0, 0.0, 0.0, 0.0);
        let s2 = s[j] * s[j];
        for c in 0..k {
            let w = row[c] * pi[c] / tot; if w == 0.0 { continue; }
            let v = scale[c] * scale[c]; let sig2 = s2 + v;
            let cm = x[j] * v / sig2; let cv = s2 * v / sig2;
            m1 += w * cm; m2 += w * (cm * cm + cv);
            if cv > 0.0 { ppos += w * 0.5 * libm::erfc(-cm / cv.sqrt() / std::f64::consts::SQRT_2); }
            if scale[c] == 0.0 { pz += w; }
        }
        pm[j] = m1; psd[j] = (m2 - m1 * m1).max(0.0).sqrt();
        lfsr[j] = pz + (1.0 - ppos - pz).min(ppos);
    }
    loglik -= n as f64 * (2.0 * std::f64::consts::PI).ln() / 2.0;
    Fit { pi, loglik, post_mean: pm, post_sd: psd, lfsr, iters }
}
