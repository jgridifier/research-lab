// CLI: dl <in.txt> <out.txt> <width> <height> [weights.txt]
//   in.txt: one series per line, comma-separated y pixels; empty field or "nan" = absent column
//   out.txt: line 1 = live counts n(c), line 2 = weight mass W(c), then height rows of the density grid
// dl --bench <n> <width> <height> <chunk> : synthetic random-walk generator streamed in chunks (no file I/O)
use denselines_core::*;
use std::io::{BufRead, Write};
use std::time::Instant;
fn main() {
    let a: Vec<String> = std::env::args().collect();
    if a[1] == "--bench" {
        let (n, w, h, chunk): (usize, usize, usize, usize) = (a[2].parse().unwrap(), a[3].parse().unwrap(), a[4].parse().unwrap(), a[5].parse().unwrap());
        // SYNTHETIC: xorshift random walks, deterministic seed 20261123
        let mut st: u64 = 20261123;
        let mut rnd = move || { st ^= st << 13; st ^= st >> 7; st ^= st << 17; (st >> 11) as f64 / (1u64 << 53) as f64 };
        let t = Instant::now();
        let mut sm = Streamer::new(w, h);
        let mut done = 0;
        let mut gen_s = 0.0;
        while done < n {
            let m = chunk.min(n - done);
            let tg = Instant::now();
            let mut buf: Vec<Vec<f32>> = Vec::with_capacity(m);
            for _ in 0..m {
                let mut y = h as f64 / 2.0; let mut s = Vec::with_capacity(w);
                for _ in 0..w { y += (rnd() - 0.5) * 6.0; y = y.clamp(0.0, h as f64); s.push((y as u32) as f32); }
                buf.push(s);
            }
            gen_s += tg.elapsed().as_secs_f64();
            sm.push(&buf, None);
            done += m;
        }
        let d = sm.finish();
        let total = t.elapsed().as_secs_f64();
        let colsum: f64 = (0..h).map(|y| d.grid[y * w]).sum();
        println!("{{\"n\":{},\"width\":{},\"height\":{},\"chunk\":{},\"threads\":{},\"total_s\":{:.4},\"gen_s\":{:.4},\"density_s\":{:.4},\"colsum0\":{}}}",
            n, w, h, chunk, rayon::current_num_threads(), total, gen_s, total - gen_s, colsum);
        return;
    }
    let (inp, out, w, h): (&str, &str, usize, usize) = (&a[1], &a[2], a[3].parse().unwrap(), a[4].parse().unwrap());
    let f = std::io::BufReader::new(std::fs::File::open(inp).unwrap());
    let data: Vec<Vec<f32>> = f.lines().map(|l| l.unwrap().split(',').map(|t| { let t = t.trim(); if t.is_empty() || t.eq_ignore_ascii_case("nan") { f32::NAN } else { t.parse().unwrap() } }).collect()).collect();
    let wts: Option<Vec<f64>> = a.get(5).map(|p| std::fs::read_to_string(p).unwrap().split_whitespace().map(|t| t.parse().unwrap()).collect());
    let t = Instant::now();
    let d = density(&data, wts.as_deref(), w, h);
    eprintln!("core_seconds {}", t.elapsed().as_secs_f64());
    let mut o = std::io::BufWriter::new(std::fs::File::create(out).unwrap());
    writeln!(o, "{}", d.live.iter().map(|v| v.to_string()).collect::<Vec<_>>().join(",")).unwrap();
    writeln!(o, "{}", d.wmass.iter().map(|v| format!("{:e}", v)).collect::<Vec<_>>().join(",")).unwrap();
    for y in 0..h { writeln!(o, "{}", (0..w).map(|x| format!("{:e}", d.grid[y * w + x])).collect::<Vec<_>>().join(",")).unwrap(); }
}
