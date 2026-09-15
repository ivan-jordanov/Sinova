import { useMemo, useRef, useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { Box, Group, LoadingOverlay, Text } from "@mantine/core";
import flatTo2DMatrix from "../../utils/matrix";
import type { ProjectionViewerProps } from "../../types/preview";
import { useViewerStore } from "../../store/viewerStore";
import { useDatasetStore } from "../../store/datasetStore";

export function ProjectionViewer({ data, isLoading, colormap = "Greys" }: ProjectionViewerProps) {
  const beamMask = useViewerStore((state) => state.beamMask);
  const setBeamMask = useViewerStore((state) => state.setBeamMask);
  const resetCounter = useViewerStore((state) => state.resetCounter);
  const setDatasetBeamMask = useDatasetStore((state) => state.setBeamMask);
  const maskParams = beamMask[1];

  const [showCircle, setShowCircle] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

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
          backgroundColor: "#d3d5db",
        }}
      >
        <Plot
          key={`projection-${colormap}-${data?.width}-${data?.height}`}
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
            uirevision: beamMask[0] ? "lasso-mode" : resetCounter,
            autosize: true,
            margin: { l: 0, r: 0, t: 0, b: 0 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            dragmode: beamMask[0] ? "lasso" : "zoom",
            xaxis: { visible: false, autorange: true, fixedrange: false },
            yaxis: { visible: false, autorange: "reversed", fixedrange: false },
            shapes:
              beamMask[0] && maskParams?.radius && showCircle
                ? [
                    {
                      type: "circle",
                      xref: "x",
                      yref: "y",
                      x0: maskParams.cx - maskParams.radius,
                      y0: maskParams.cy - maskParams.radius,
                      x1: maskParams.cx + maskParams.radius,
                      y1: maskParams.cy + maskParams.radius,
                      line: { color: "#ff0000", width: 2 },
                    },
                  ]
                : [],
          }}
          config={{ displayModeBar: false, responsive: true, doubleClick: false, showTips: false }}
          onSelected={(e: any) => {
            if (!beamMask[0] || !e?.lassoPoints?.x?.length) return;

            const xs: number[] = e.lassoPoints.x;
            const ys: number[] = e.lassoPoints.y;
            const len = xs.length;

            const cx = xs.reduce((sum, val) => sum + val, 0) / len;
            const cy = ys.reduce((sum, val) => sum + val, 0) / len;

            const radius =
              xs.reduce((sum, x, i) => sum + Math.hypot(x - cx, ys[i] - cy), 0) / len;

            setBeamMask([true, { cx, cy, radius }]);

            setDatasetBeamMask({ cx, cy, radius });

            setShowCircle(true);
            if (timerRef.current) clearTimeout(timerRef.current);
            timerRef.current = setTimeout(() => {
              setShowCircle(false);
            }, 3000);
          }}
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