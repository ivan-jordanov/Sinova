import { useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { Box, Group, Text, Badge, SegmentedControl, Center } from "@mantine/core";
import type { LineProfileProps } from "../../types/preview";
import flatTo2DMatrix from "../../utils/matrix";
import { calculateImageStats, computeHistogram, computeMeanProfiles } from "../../utils/statistics";


export function GlobalAnalysis({ data, isLoading }: LineProfileProps) {
  const [activeTab, setActiveTab] = useState<string>("histogram");
  const [profileAxis, setProfileAxis] = useState<"row" | "col">("row");

  const { stats, histogram, profiles } = useMemo(() => {
    // Validate preview data payload
    if (!data || !data.data || !data.width || !data.height) {
      return { stats: null, histogram: null, profiles: null };
    }

    const pixels = data.data;
    if (pixels.length === 0 || pixels.length !== data.width * data.height) {
      return { stats: null, histogram: null, profiles: null };
    }

    const imgStats = calculateImageStats(pixels);
    const hist = computeHistogram(pixels, imgStats.min, imgStats.max, 64);
    
    const matrix2D = flatTo2DMatrix(pixels, data.width, data.height);
    const profs = computeMeanProfiles(matrix2D, data.width, data.height);

    return { stats: imgStats, histogram: hist, profiles: profs };
  }, [data]);

  const hasData = Boolean(stats && histogram && profiles);

  return (
    <Box pt="md" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.08)", width: "100%" }}>
      <Group justify="space-between" align="center" mb="xs" wrap="nowrap">
        <Group gap="xs" align="center" style={{ overflow: "hidden" }}>
          <Text size="xs" c="dimmed" fw={600} style={{ letterSpacing: 0.8, shrink: 0 }}>
            GLOBAL ANALYSIS
          </Text>
          {hasData && stats && (
            <Group gap={6} wrap="nowrap">
              <Badge variant="subtle" color="gray" size="xs">
                Min: {stats.min.toFixed(1)}
              </Badge>
              <Badge variant="subtle" color="gray" size="xs">
                Max: {stats.max.toFixed(1)}
              </Badge>
              <Badge variant="subtle" color="blue" size="xs">
                μ: {stats.mean.toFixed(1)}
              </Badge>
              <Badge variant="subtle" color="teal" size="xs">
                σ: {stats.stdDev.toFixed(1)}
              </Badge>
              <Badge variant="subtle" color="cyan" size="xs">
                SNR: {stats.snr.toFixed(1)}
              </Badge>
            </Group>
          )}
        </Group>

        <Group gap="xs" style={{ shrink: 0 }}>
          {activeTab === "profile" && hasData && (
            <SegmentedControl
              size="xs"
              value={profileAxis}
              onChange={(val) => setProfileAxis(val as "row" | "col")}
              data={[
                { label: "Row", value: "row" },
                { label: "Col", value: "col" },
              ]}
            />
          )}

          <SegmentedControl
            size="xs"
            value={activeTab}
            onChange={setActiveTab}
            data={[
              { label: "Histogram", value: "histogram" },
              { label: "Mean Profile", value: "profile" },
            ]}
          />
        </Group>
      </Group>

      <Box style={{ width: "100%", height: "160px", position: "relative" }}>
        {hasData && activeTab === "histogram" && (
          <Plot
            data={[
              {
                x: histogram!.x,
                y: histogram!.y,
                type: "bar",
                marker: { color: "#22d3ee" },
              },
            ]}
            layout={{
              autosize: true,
              margin: { l: 40, r: 10, t: 10, b: 25 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              xaxis: { color: "#a1a1aa", gridcolor: "rgba(255,255,255,0.05)" },
              yaxis: { color: "#a1a1aa", gridcolor: "rgba(255,255,255,0.05)" },
              bargap: 0.1,
            }}
            config={{ displayModeBar: false, responsive: true }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        )}

        {hasData && activeTab === "profile" && (
          <Plot
            data={[
              {
                y: profileAxis === "row" ? profiles!.rowMeans : profiles!.colMeans,
                type: "scatter",
                mode: "lines",
                line: { color: "#22d3ee", width: 1.5 },
                fill: "tozeroy",
                fillcolor: "rgba(34, 211, 238, 0.08)",
              },
            ]}
            layout={{
              autosize: true,
              margin: { l: 40, r: 10, t: 10, b: 25 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              xaxis: { color: "#a1a1aa", gridcolor: "rgba(255,255,255,0.05)" },
              yaxis: { color: "#a1a1aa", gridcolor: "rgba(255,255,255,0.05)" },
            }}
            config={{ displayModeBar: false, responsive: true }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        )}

        {!hasData && (
          <Center style={{ height: "100%", width: "100%" }}>
            <Text size="xs" c="dimmed">
              {isLoading ? "Calculating analysis..." : "No active preview data loaded"}
            </Text>
          </Center>
        )}
      </Box>
    </Box>
  );
}