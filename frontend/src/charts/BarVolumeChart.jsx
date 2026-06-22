import { useEffect, useRef } from "react";
import { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip } from "chart.js";
import { baseCartesianOptions, CHART_COLORS, formatChartDate } from "./chartTheme";

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);

export function BarVolumeChart({ data, loading }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (loading || !canvasRef.current || !data?.length) {
      return undefined;
    }
    const sorted = [...data].sort((a, b) => new Date(a.day) - new Date(b.day));

    if (chartRef.current) {
      chartRef.current.destroy();
    }
    chartRef.current = new Chart(canvasRef.current, {
      type: "bar",
      data: {
        labels: sorted.map((item) => formatChartDate(item.day)),
        datasets: [
          {
            label: "New cases",
            data: sorted.map((item) => item.volume),
            backgroundColor: CHART_COLORS.bar,
            borderRadius: 4,
            maxBarThickness: 40,
          },
        ],
      },
      options: {
        ...baseCartesianOptions({ yLabel: "Cases" }),
        plugins: {
          ...baseCartesianOptions().plugins,
          tooltip: {
            ...baseCartesianOptions().plugins.tooltip,
            callbacks: {
              label: (ctx) => `${ctx.parsed.y} case${ctx.parsed.y === 1 ? "" : "s"}`,
            },
          },
        },
      },
    });
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data, loading]);

  if (loading) {
    return <div className="cv-chart-canvas cv-chart-skeleton" />;
  }
  if (!data?.length) {
    return <p className="cv-chart-empty">No new cases this week yet.</p>;
  }
  return (
    <div className="cv-chart-canvas">
      <canvas ref={canvasRef} />
    </div>
  );
}
