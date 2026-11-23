//! Gap-safe, weighted, streaming DenseLines core (independent re-implementation; research prototype).
//! Raster semantics follow the reference (line-density-rust @083890c, imageproc 0.25 BresenhamLineIter,
//! f32 error term, truncating casts, out-of-canvas pixels dropped, pixel SET not incremented). Each series'
//! pixel set is normalised per column by its own count; columns it does not cover contribute 0 (0/0 := 0).
//! Per-series weights scale the contribution. Series are streamed: no per-series image is ever stored.
use rayon::prelude::*;

pub struct Density {
    pub width: usize,
    pub height: usize,
    /// row-major (height x width) weighted density
    pub grid: Vec<f64>,
    /// n(c): number of series with >= 1 pixel in column c
    pub live: Vec<u64>,
    /// W(c): weight mass of series live in column c
    pub wmass: Vec<f64>,
}

#[inline]
fn bresenham(x0: f32, y0: f32, x1: f32, y1: f32, w: i64, h: i64, out: &mut Vec<(u32, u32)>) {
    let steep = (y1 - y0).abs() > (x1 - x0).abs();
    let (mut ax, mut ay, mut bx, mut by) = if steep { (y0, x0, y1, x1) } else { (x0, y0, x1, y1) };
    if ax > bx { std::mem::swap(&mut ax, &mut bx); std::mem::swap(&mut ay, &mut by); }
    let dx = bx - ax;
    let dy = (by - ay).abs();
    let mut err = dx / 2.0f32;
    let mut y = ay as i32 as i64;
    let ystep: i64 = if ay < by { 1 } else { -1 };
    let mut x = ax as i32 as i64;
    let end_x = bx as i32 as i64;
    while x <= end_x {
        let (px, py) = if steep { (y, x) } else { (x, y) };
        if px >= 0 && px < w && py >= 0 && py < h { out.push((px as u32, py as u32)); }
        x += 1;
        err -= dy;
        if err < 0.0 { y += ystep; err += dx; }
    }
}

struct Acc { grid: Vec<f64>, live: Vec<u64>, wmass: Vec<f64>, px: Vec<(u32, u32)>, cnt: Vec<u32> }

impl Acc {
    fn new(w: usize, h: usize) -> Self {
        Acc { grid: vec![0.0; w * h], live: vec![0; w], wmass: vec![0.0; w], px: Vec::new(), cnt: vec![0; w] }
    }
    fn add(&mut self, s: &[f32], wt: f64, w: usize, h: usize) {
        // a series is a run of finite y-pixels; NaN (absent) breaks the line: no segment touches a NaN vertex
        self.px.clear();
        for x in 0..s.len().saturating_sub(1) {
            let (a, b) = (s[x], s[x + 1]);
            if a.is_finite() && b.is_finite() {
                bresenham(x as f32, a, (x + 1) as f32, b, w as i64, h as i64, &mut self.px);
            }
        }
        if self.px.is_empty() { return; }
        self.px.sort_unstable();
        self.px.dedup();
        for &(x, _) in &self.px { self.cnt[x as usize] += 1; }
        for &(x, y) in &self.px {
            let c = self.cnt[x as usize] as f64;
            self.grid[y as usize * w + x as usize] += wt / c;
        }
        let mut last = u32::MAX;
        for &(x, _) in &self.px {
            if x != last { self.live[x as usize] += 1; self.wmass[x as usize] += wt; self.cnt[x as usize] = 0; last = x; }
        }
    }
    fn merge(mut self, o: Acc) -> Acc {
        for (a, b) in self.grid.iter_mut().zip(o.grid) { *a += b; }
        for (a, b) in self.live.iter_mut().zip(o.live) { *a += b; }
        for (a, b) in self.wmass.iter_mut().zip(o.wmass) { *a += b; }
        self
    }
}

/// `series[i]` holds y-pixels (vertex x = column index); f32::NAN marks an absent column.
/// `weights` defaults to 1 for every series.
pub fn density<S: AsRef<[f32]> + Sync>(series: &[S], weights: Option<&[f64]>, width: usize, height: usize) -> Density {
    let acc = series
        .par_iter()
        .enumerate()
        .fold(|| Acc::new(width, height), |mut a, (i, s)| {
            let wt = weights.map_or(1.0, |w| w[i]);
            a.add(s.as_ref(), wt, width, height);
            a
        })
        .reduce(|| Acc::new(width, height), |a, b| a.merge(b));
    Density { width, height, grid: acc.grid, live: acc.live, wmass: acc.wmass }
}

/// Streaming entry point: feed chunks from any producer; memory is O(threads x width x height + chunk).
pub struct Streamer { w: usize, h: usize, acc: Option<Acc> }
impl Streamer {
    pub fn new(width: usize, height: usize) -> Self { Streamer { w: width, h: height, acc: Some(Acc::new(width, height)) } }
    pub fn push<S: AsRef<[f32]> + Sync>(&mut self, chunk: &[S], weights: Option<&[f64]>) {
        let d = density(chunk, weights, self.w, self.h);
        let a = self.acc.as_mut().unwrap();
        for (x, y) in a.grid.iter_mut().zip(d.grid) { *x += y; }
        for (x, y) in a.live.iter_mut().zip(d.live) { *x += y; }
        for (x, y) in a.wmass.iter_mut().zip(d.wmass) { *x += y; }
    }
    pub fn finish(mut self) -> Density {
        let a = self.acc.take().unwrap();
        Density { width: self.w, height: self.h, grid: a.grid, live: a.live, wmass: a.wmass }
    }
}
