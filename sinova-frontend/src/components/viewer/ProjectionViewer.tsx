import Plot from "react-plotly.js";
import { Box, Text } from "@mantine/core";
const values = Array.from({ length: 38 }, (_, row) =>
  Array.from({ length: 64 }, (_, column) =>
    Math.max(0, Math.sin(column / 9) + Math.cos(row / 6) + 1.3),
  ),
);
export function ProjectionViewer() {
  return (
    <Box className="plot-wrap">
      {/* Plotly's z matrix is the future ArrayBuffer-to-pixel rendering boundary. */}
      <Plot
        data={[
          {
            z: values,
            type: "heatmapgl",
            colorscale: "Gray",
            showscale: false,
          },
        ]}
        layout={{
          autosize: true,
          margin: { l: 8, r: 8, t: 8, b: 8 },
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
        PROJECTION · MOCK FRAME · DETECTOR 2048 × 2048
      </Text>
    </Box>
  );
}
