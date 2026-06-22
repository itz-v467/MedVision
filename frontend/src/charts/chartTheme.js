export const CHART_COLORS = {
  primary: "#4a7a73",
  accent: "#5d8f87",
  fill: "rgba(74, 122, 115, 0.12)",
  bar: "#6a9e96",
  grid: "rgba(74, 122, 115, 0.1)",
};

export const chartFont = {
  family: "'Inter', system-ui, sans-serif",
  size: 11,
};

export function formatChartDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

export function baseCartesianOptions({ yLabel, xLabel } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#1b1c1c",
        padding: 10,
        cornerRadius: 6,
        titleFont: { size: 12, weight: "600" },
        bodyFont: { size: 11 },
      },
    },
    scales: {
      x: {
        title: xLabel
          ? { display: true, text: xLabel, font: { size: 11 }, color: "#73787a" }
          : undefined,
        grid: { display: false },
        border: { display: false },
        ticks: {
          font: chartFont,
          color: "#73787a",
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 8,
        },
      },
      y: {
        title: yLabel
          ? { display: true, text: yLabel, font: { size: 11 }, color: "#73787a" }
          : undefined,
        beginAtZero: true,
        grid: { color: CHART_COLORS.grid },
        border: { display: false },
        ticks: {
          font: chartFont,
          color: "#73787a",
          precision: 0,
          padding: 6,
        },
      },
    },
  };
}
