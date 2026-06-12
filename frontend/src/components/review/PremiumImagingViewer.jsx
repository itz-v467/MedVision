import { useState } from "react";
import { HeatmapImage } from "../HeatmapImage";
import { ImagingFindingsTable } from "../ImagingFindingsTable";

export function PremiumImagingViewer({ imaging }) {
  const [heatmapOpacity, setHeatmapOpacity] = useState(55);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [zoom, setZoom] = useState(1);

  if (!imaging) return null;

  const findings = imaging.findings
    ? Object.entries(imaging.findings).sort((a, b) => (b[1].probability ?? 0) - (a[1].probability ?? 0))
    : [];

  return (
    <section className="cv-section" aria-labelledby="imaging-heading">
      <h2 className="cv-section-title" id="imaging-heading">Imaging validation</h2>
      <p className="cv-section-sub">
        Verify AI predictions against source imaging. Model {imaging.model_version || "v1"} ·{" "}
        {((imaging.confidence ?? 0) * 100).toFixed(0)}% confidence
      </p>

      <div className="cv-imaging-section">
        <div
          className="cv-imaging-viewport"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "center center",
            transition: "transform 200ms ease",
          }}
        >
          {imaging.heatmap_url && showHeatmap && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "radial-gradient(circle at 55% 65%, rgba(255,60,0,0.5) 0%, transparent 60%)",
                mixBlendMode: "screen",
                opacity: heatmapOpacity / 100,
                pointerEvents: "none",
                zIndex: 2,
              }}
            />
          )}
          <div
            style={{
              width: "100%",
              minHeight: 480,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              background: "linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%)",
            }}
          >
            <HeatmapImage url={imaging.heatmap_url} />
            {!imaging.heatmap_url && (
              <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "var(--cv-text-sm)" }}>
                Chest radiograph viewport
              </span>
            )}
          </div>
        </div>

        <div className="cv-imaging-controls">
          <label>
            Heatmap
            <input
              type="range"
              min={0}
              max={100}
              value={heatmapOpacity}
              onChange={(e) => setHeatmapOpacity(Number(e.target.value))}
              disabled={!showHeatmap}
            />
            {heatmapOpacity}%
          </label>
          <button
            type="button"
            className="cv-btn cv-btn-sm cv-btn-secondary"
            onClick={() => setShowHeatmap((v) => !v)}
          >
            {showHeatmap ? "Hide overlay" : "Show overlay"}
          </button>
          <button type="button" className="cv-btn cv-btn-sm cv-btn-secondary" onClick={() => setZoom((z) => Math.min(z + 0.25, 3))}>
            Zoom in
          </button>
          <button type="button" className="cv-btn cv-btn-sm cv-btn-secondary" onClick={() => setZoom((z) => Math.max(z - 0.25, 0.5))}>
            Zoom out
          </button>
          <button type="button" className="cv-btn cv-btn-sm cv-btn-ghost" onClick={() => setZoom(1)}>
            Reset view
          </button>
        </div>
      </div>

      <div style={{ marginTop: "var(--cv-space-3)" }}>
        <ImagingFindingsTable findings={imaging.findings || {}} />
      </div>

      {findings.length > 0 && (
        <div className="cv-panel cv-panel-pad" style={{ marginTop: "var(--cv-space-2)" }}>
          <h4 style={{ margin: "0 0 12px", fontSize: "var(--cv-text-sm)", fontWeight: 600 }}>
            Disease predictions
          </h4>
          {findings.map(([name, data]) => {
            const prob = (data.probability ?? 0) * 100;
            return (
              <div key={name} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--cv-text-sm)", marginBottom: 4 }}>
                  <span>{name.replace(/_/g, " ")}</span>
                  <span style={{ fontWeight: 600 }}>{prob.toFixed(1)}%</span>
                </div>
                <div style={{ height: 4, background: "var(--cv-slate-200)", borderRadius: 999 }}>
                  <div style={{ height: "100%", width: `${prob}%`, background: "var(--cv-primary)", borderRadius: 999 }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
