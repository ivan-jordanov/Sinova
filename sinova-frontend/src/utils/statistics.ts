import type { ImageStats } from "../types/preview";

export function calculateImageStats(data: ArrayLike<number>): ImageStats {
  if (!data || data.length === 0) {
    return { min: 0, max: 0, mean: 0, stdDev: 0, snr: 0 };
  }

  let sum = 0;
  let min = data[0];
  let max = data[0];

  for (let i = 0; i < data.length; i++) {
    const v = data[i];
    sum += v;
    if (v < min) min = v;
    if (v > max) max = v;
  }

  const mean = sum / data.length;
  let sumSq = 0;

  for (let i = 0; i < data.length; i++) {
    sumSq += (data[i] - mean) ** 2;
  }

  const variance = sumSq / data.length;
  const stdDev = Math.sqrt(variance);
  const snr = stdDev === 0 ? 0 : mean / stdDev;

  return { min, max, mean, stdDev, snr };
}

export function computeHistogram(data: ArrayLike<number>, min: number, max: number, bins = 64) {
  const counts = new Array(bins).fill(0);
  const range = max - min;
  
  if (range === 0) return { x: [min], y: [data.length] };

  for (let i = 0; i < data.length; i++) {
    let bin = Math.floor(((data[i] - min) / range) * bins);
    if (bin >= bins) bin = bins - 1;
    counts[bin]++;
  }

  const binEdges = Array.from({ length: bins }, (_, i) => min + (i + 0.5) * (range / bins));
  return { x: binEdges, y: counts };
}

export function computeMeanProfiles(matrix2D: number[][] | Float32Array[], width: number, height: number) {
  const rowMeans = new Array(height).fill(0);
  const colMeans = new Array(width).fill(0);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const val = matrix2D[y][x];
      rowMeans[y] += val;
      colMeans[x] += val;
    }
    rowMeans[y] /= width;
  }

  for (let x = 0; x < width; x++) {
    colMeans[x] /= height;
  }

  return { rowMeans, colMeans };
}