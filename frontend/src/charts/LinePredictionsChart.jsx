import { useEffect, useRef } from "react";
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend } from "chart.js";

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend);

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
        labels: data.map((item) => item.date),
        datasets: [
          {
            label: "Daily Predictions",
            data: data.map((item) => item.count),
            borderColor: "#0ea5e9",
            backgroundColor: "rgba(14,165,233,0.2)",
            tension: 0.3,
          },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data, loading]);

  if (loading) {
    return <div className="chart-skeleton" />;
  }
  return <div className="chart-box"><canvas ref={canvasRef} /></div>;
}
