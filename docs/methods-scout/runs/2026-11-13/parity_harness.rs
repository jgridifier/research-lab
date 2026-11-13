// Parity harness: same run_series/sum_images as upstream src/main.rs, but reads series from a file
// (one series per line, comma-separated u32 y-pixels, one per column) and writes the raw f32 density.
use image::{ImageBuffer, Luma};
use imageproc::drawing::draw_line_segment_mut;
use rayon::prelude::*;
use std::io::{BufRead, Write};
use std::time::Instant;
type Image = ImageBuffer<Luma<f32>, Vec<f32>>;
fn run_series(series: &[u32], width: u32, height: u32) -> Image {
    let mut data = Image::new(width, height);
    for x in 0..series.len() - 1 {
        draw_line_segment_mut(&mut data,(x as f32, series[x] as f32),((x + 1) as f32, series[x + 1] as f32),Luma([1.0]));
    }
    for x in 0..width {
        let mut sum = 0.0;
        for y in 0..height { sum += data.get_pixel(x, y)[0]; }
        for y in 0..height { let v = data.get_pixel(x, y)[0]; data.put_pixel(x, y, Luma([v / sum])); }
    }
    data
}
fn sum_images(image: Image, mut agg: Image) -> Image {
    for (x, y, v) in image.enumerate_pixels() { let n = agg.get_pixel(x, y)[0] + v[0]; agg.put_pixel(x, y, Luma([n])) }
    agg
}
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let (inp, out, width, height): (&str,&str,u32,u32) = (&a[1], &a[2], a[3].parse().unwrap(), a[4].parse().unwrap());
    let f = std::io::BufReader::new(std::fs::File::open(inp).unwrap());
    let data: Vec<Vec<u32>> = f.lines().map(|l| l.unwrap().split(',').map(|t| t.trim().parse().unwrap()).collect()).collect();
    let now = Instant::now();
    let agg = data.par_iter().map(|s| run_series(s, width, height)).reduce(|| Image::new(width, height), sum_images);
    eprintln!("rust_seconds {}", now.elapsed().as_secs_f64());
    let mut o = std::io::BufWriter::new(std::fs::File::create(out).unwrap());
    for y in 0..height { let row: Vec<String> = (0..width).map(|x| format!("{:e}", agg.get_pixel(x, y)[0])).collect(); writeln!(o, "{}", row.join(",")).unwrap(); }
}
