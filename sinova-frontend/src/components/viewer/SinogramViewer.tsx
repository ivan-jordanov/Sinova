import { useMemo } from "react";
import Plot from "react-plotly.js";
import { Box, Group, LoadingOverlay, Text } from "@mantine/core";
import flatTo2DMatrix from "../../utils/matrix";
import type { SinogramViewerProps } from "../../types/preview";
import { useViewerStore } from "../../store/viewerStore";


 // Non working plotly resizing mess, need to fix
export function SinogramViewer({
  data,
  isLoading,
  colormap = "Greys",
}: SinogramViewerProps) {
  const resetCounter = useViewerStore((state) => state.resetCounter);
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
      <LoadingOverlay
        visible={isLoading}
        overlayProps={{ blur: 1 }}
        zIndex={10}
      />

      <Box
        style={{
          width: "100%",
          aspectRatio: hasData ? `${data!.width} / ${data!.height}` : "16 / 9",
          minHeight: hasData ? "auto" : "300px",
          position: "relative",
          backgroundColor: "#d3d5db",
        }}
      >
        <Plot
          // 1. REMOVE resetCounter from key so component isn't destroyed
          key={`sinogram-${colormap}-${data?.width}-${data?.height}`} 
          
          // 2. ADD revision prop to force react-plotly to sync updates immediately
          revision={resetCounter} 
          
          data={
            hasData
              ? [
                  {
                    z: matrix2D,
                    type: "heatmap",
                    colorscale: colormap,
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
            
            // 3. ADD uirevision for Plotly's native, seamless zoom reset
            uirevision: resetCounter, 
            
            margin: { l: 0, r: 0, t: 0, b: 0 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            xaxis: { visible: false, autorange: true, fixedrange: false },
            yaxis: { 
              visible: false, 
              autorange: "reversed", 
              fixedrange: false,
              // 4. ADD scaleanchor to force square pixels so it never stretches on resize
              scaleanchor: "x" 
            },
          }}
          config={{
            displayModeBar: false,
            responsive: true,
            doubleClick: false,
            showTips: false,
          }}
          useResizeHandler
          style={{ width: "100%", height: "100%", display: "block" }}
        />
      </Box>

      <Group justify="space-between" align="center" px="xs" py={4} w="100%">
        <Text size="xs" c="dimmed">
          SINOGRAM · {data ? `${data.width} × ${data.height}` : "IDLE"}
        </Text>
      </Group>
    </Box>
  );
}