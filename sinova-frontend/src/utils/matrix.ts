export function flatTo2DMatrix(
  flatData: Float32Array | number[],
  width: number,
  height: number
): number[][] {
  if (!flatData || flatData.length === 0 || width <= 0 || height <= 0) {
    return [];
  }

  const matrix: number[][] = new Array(height);
  for (let y = 0; y < height; y++) {
    const row = new Array(width);
    const offset = y * width;
    for (let x = 0; x < width; x++) {
      row[x] = flatData[offset + x] ?? 0;
    }
    matrix[y] = row;
  }
  return matrix;
}

export default flatTo2DMatrix;