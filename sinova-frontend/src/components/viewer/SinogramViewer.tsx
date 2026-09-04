import Plot from "react-plotly.js";
import { Box, Text } from "@mantine/core";
const values = Array.from({ length: 42 }, (_, row) =>
  Array.from(
    { length: 90 },
    (_, column) =>
      Math.sin(column / 12) * 0.28 +
      Math.cos(row / 8) * 0.24 +
      Math.sin((row + column) / 17) * 0.08,
  ),
);
export function SinogramViewer() {
  return (
    <Box className="plot-wrap">
      {/* Plotly receives a matrix through z: rows are detector slices and columns
          are projection positions. heatmapgl keeps large matrices GPU-friendly. */}
      <Plot
        data={[
          {
            z: values,
            type: "heatmapgl",
            colorscale: "Viridis",
            showscale: false,
          },
        ]}
        layout={{
          autosize: true,
          margin: { l: 38, r: 8, t: 8, b: 28 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          xaxis: { visible: false },
          yaxis: { visible: false },
          font: { color: "#758495" },
        }}
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
      <Text className="viewer-caption">
        SINOGRAM · MOCK PREVIEW · 2048 × 1800
      </Text>
    </Box>
  );
}
