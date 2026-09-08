import { useMemo } from "react";
import Plot from "react-plotly.js";
import { Box, Group, LoadingOverlay, Text } from "@mantine/core";
import type { PreviewResult } from "../../types/preview";
import flatTo2DMatrix from "../../utils/matrix";

interface ProjectionViewerProps {
  data?: PreviewResult;
  isLoading: boolean;
}

export function ProjectionViewer({ data, isLoading }: ProjectionViewerProps) {
  const matrix2D = useMemo(() => {
    if (!data?.data || !data.width || !data.height) return [];
    return flatTo2DMatrix(data.data, data.width, data.height);
  }, [data]);

  const hasData = Boolean(data && matrix2D.length > 0);

  return (
    <Box
      pos="relative"
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <LoadingOverlay visible={isLoading} overlayProps={{ blur: 1 }} zIndex={10} />

      <Box
        style={{
          width: "100%",
          aspectRatio: hasData ? `${data!.width} / ${data!.height}` : "16 / 9",
          minHeight: hasData ? "auto" : "300px",
          position: "relative",
          backgroundColor: "#1a1b1e",
        }}
      >
        <Plot
          data={
            hasData
              ? [
                  {
                    z: matrix2D,
                    type: "heatmap",
                    colorscale: "Greys",
                    showscale: false,
                    zauto: false,
                    zmin: data!.minVal,
                    zmax: data!.maxVal,
                  },
                ]
              : []
          }
          layout={{
            autosize: true,
            margin: { l: 0, r: 0, t: 0, b: 0 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            xaxis: { visible: false, autorange: true, fixedrange: false },
            yaxis: { visible: false, autorange: "reversed", fixedrange: false },
          }}
          // doubleClick: false stops the glitching behavior caused by double-clicking
          config={{ displayModeBar: false, responsive: true, doubleClick: false, showTips: false }}
          useResizeHandler
          style={{ width: "100%", height: "100%", display: "block" }}
        />
      </Box>

      <Group justify="space-between" align="center" px="xs" py={4} w="100%">
        <Text size="xs" c="dimmed">
          PROJECTION · {data ? `${data.width} × ${data.height}` : "IDLE"}
        </Text>
      </Group>
    </Box>
  );
}