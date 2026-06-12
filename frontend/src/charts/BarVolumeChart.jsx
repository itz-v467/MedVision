import { useEffect, useRef } from "react";
import { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip, Legend } from "chart.js";

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

export function BarVolumeChart({ data, loading }) {
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
      type: "bar",
      data: {
        labels: data.map((item) => item.day),
        datasets: [
          {
            label: "Weekly Analysis Volume",
            data: data.map((item) => item.volume),
            backgroundColor: "#6366f1",
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
