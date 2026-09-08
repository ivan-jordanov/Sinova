import { useMemo } from "react";
import Plot from "react-plotly.js";
import { Box, LoadingOverlay, Text } from "@mantine/core";
import type { PreviewResult } from "../../types/preview";
import flatTo2DMatrix from "../../utils/matrix";

interface SinogramViewerProps {
  data?: PreviewResult;
  isLoading: boolean;
}

export function SinogramViewer({ data, isLoading }: SinogramViewerProps) {
  const matrix2D = useMemo(() => {
    if (!data) return [];
    return flatTo2DMatrix(data.data, data.width, data.height);
  }, [data]);

  return (
    <Box className="plot-wrap" pos="relative">
      <LoadingOverlay visible={isLoading} overlayProps={{ blur: 1 }} />
      {data && (
        <Plot
          data={[
            {
              z: matrix2D,
              type: "heatmapgl",
              colorscale: "Viridis",
              showscale: false,
              zmin: data.minVal,
              zmax: data.maxVal,
            },
          ]}
          layout={{
            autosize: true,
            margin: { l: 8, r: 8, t: 8, b: 8 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            xaxis: { visible: false },
            yaxis: { visible: false, autorange: "reversed" },
            font: { color: "#758495" },
          }}
          config={{ displayModeBar: false, responsive: true }}
          useResizeHandler
          style={{ width: "100%", height: "100%" }}
        />
      )}
      <Text className="viewer-caption">
        SINOGRAM · {data ? `${data.width} × ${data.height}` : "LOADING"}
      </Text>
    </Box>
  );
}