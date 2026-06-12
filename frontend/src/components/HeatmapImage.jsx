import { useEffect, useState } from "react";
import { HttpClient } from "../services/httpClient";

export function HeatmapImage({ url, alt = "Explainability heatmap" }) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!url) {
      setSrc(null);
      return undefined;
    }

    let objectUrl = null;
    setError("");
    HttpClient.requestBlob(url)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch((err) => {
        setError(err.message || "Heatmap unavailable.");
        setSrc(null);
      });

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [url]);

  if (!url) {
    return <p className="empty-state">No heatmap generated for this study.</p>;
  }
  if (error) {
    return <p className="empty-state">{error}</p>;
  }
  if (!src) {
    return <div className="chart-skeleton heatmap-skeleton" />;
  }
  return <img className="heatmap-image" src={src} alt={alt} />;
}
