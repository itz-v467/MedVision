import { useEffect, useRef } from "react";
import { ArcElement, Chart, DoughnutController, Legend, Tooltip } from "chart.js";

Chart.register(DoughnutController, ArcElement, Tooltip, Legend);

export function DoughnutAbnormalityChart({ data, loading }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (loading || !canvasRef.current || !data) {
      return undefined;
    }
    const labels = Object.keys(data);
    const values = Object.values(data);
    if (!labels.length) {
      return undefined;
    }
    if (chartRef.current) {
      chartRef.current.destroy();
    }
    chartRef.current = new Chart(canvasRef.current, {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            label: "Abnormality Distribution",
            data: values,
            backgroundColor: ["#ef4444", "#f59e0b", "#10b981", "#3b82f6"],
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
