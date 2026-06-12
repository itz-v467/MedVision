import { useEffect, useRef } from "react";
import {
  Chart,
  LinearScale,
  PointElement,
  ScatterController,
  Tooltip,
  Legend,
} from "chart.js";

Chart.register(ScatterController, PointElement, LinearScale, Tooltip, Legend);

export function ScatterConfidenceChart({ data, loading }) {
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
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Model Confidence",
            data: data.map((item) => ({ x: item.x, y: item.y })),
            backgroundColor: "#14b8a6",
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
