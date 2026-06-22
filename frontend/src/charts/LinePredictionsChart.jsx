import { useEffect, useRef } from "react";
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Filler } from "chart.js";
import { baseCartesianOptions, CHART_COLORS, formatChartDate } from "./chartTheme";

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Filler);

export function LinePredictionsChart({ data, loading }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (loading || !canvasRef.current || !data?.length) {
      return undefined;
    }
    if (chartRef.current) {
      chartRef.current.destroy();
    }
    chartRef.current = new Chart(canvasRef.current, {
      type: "line",
      data: {
        labels: data.map((item) => formatChartDate(item.date)),
        datasets: [
          {
            label: "AI analyses",
            data: data.map((item) => item.count),
            borderColor: CHART_COLORS.primary,
            backgroundColor: CHART_COLORS.fill,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: CHART_COLORS.primary,
            tension: 0.35,
            fill: true,
          },
        ],
      },
      options: {
        ...baseCartesianOptions({ yLabel: "Analyses" }),
        plugins: {
          ...baseCartesianOptions().plugins,
          tooltip: {
            ...baseCartesianOptions().plugins.tooltip,
            callbacks: {
              label: (ctx) => `${ctx.parsed.y} analysis${ctx.parsed.y === 1 ? "" : "es"}`,
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
    return <p className="cv-chart-empty">No AI analysis history yet — charts appear after cases are processed.</p>;
  }
  return (
    <div className="cv-chart-canvas">
      <canvas ref={canvasRef} />
    </div>
  );
}
