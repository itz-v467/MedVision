import { useEffect, useMemo, useRef, useState } from "react";
import { ClinicalBlobImage } from "./ClinicalBlobImage";
import { ImagingFindingsTable } from "../ImagingFindingsTable";

const FINDING_LABELS = {
  pneumothorax: "Pneumothorax",
  opacity: "Lung opacity / pneumonia",
  pleural_effusion: "Pleural effusion",
  nodule: "Lung nodule",
  cardiomegaly: "Cardiomegaly",
};

function ProofRow({ label, value, tone }) {
  return (
    <div className={`cv-imaging-proof-row${tone ? ` is-${tone}` : ""}`}>
      <span className="cv-imaging-proof-label">{label}</span>
      <span className="cv-imaging-proof-value">{value}</span>
    </div>
  );
}

function imagingStatusMessage(status) {
  const map = {
    ready: "Imaging localization ready — anomaly box aligned to the scan.",
    no_regions: "Scan analyzed but no anomaly box was returned. Re-upload or check server logs.",
    image_load_failed: "Source image could not be loaded — box cannot be shown.",
    skipped: "Imaging was skipped for this encounter (not a chest X-ray case).",
  };
  return map[status] || "Imaging status unknown.";
}

function imagingStatusTone(status) {
  if (status === "ready") return "ok";
  if (status === "skipped") return undefined;
  return "warn";
}

export function PremiumImagingViewer({ imaging, fileName, onReanalyze, reanalyzing = false }) {
  const [heatmapOpacity, setHeatmapOpacity] = useState(45);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showRegions, setShowRegions] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [sourceLoaded, setSourceLoaded] = useState(false);
  const [imageLoadFailed, setImageLoadFailed] = useState(false);
  const [frameSize, setFrameSize] = useState(null);
  const stackRef = useRef(null);
  const imageRef = useRef(null);

  const proof = imaging?.proof || {};
  const regions = Array.isArray(imaging?.regions) ? imaging.regions : [];
  const imagingStatus = imaging?.imaging_status || proof.imaging_status || (
    regions.length ? "ready" : sourceLoaded ? "no_regions" : imageLoadFailed ? "image_load_failed" : undefined
  );
  const findings = useMemo(
    () =>
      imaging?.findings
        ? Object.entries(imaging.findings)
            .filter(([key]) => !key.startsWith("_"))
            .sort((a, b) => (b[1].probability ?? 0) - (a[1].probability ?? 0))
        : [],
    [imaging?.findings]
  );

  const syncFrameFromImage = (img) => {
    if (!img) return;
    imageRef.current = img;
    setFrameSize({ width: img.clientWidth, height: img.clientHeight });
  };

  useEffect(() => {
    const img = imageRef.current;
    const stack = stackRef.current;
    if (!img || !stack) return undefined;

    const update = () => syncFrameFromImage(img);
    update();

    const observer = typeof ResizeObserver !== "undefined"
      ? new ResizeObserver(update)
      : null;
    observer?.observe(img);
    window.addEventListener("resize", update);

    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", update);
    };
  }, [sourceLoaded, imaging?.image_url]);

  if (!imaging) return null;

  const detected = findings.filter(([, data]) => data?.detected);
  const isFallback = proof.is_fallback || String(imaging.model_version || "").startsWith("fallback");
  const engineLabel = isFallback
    ? "Placeholder scorer (real ChestNet analysis failed or was unavailable)"
    : "TorchXRayVision / ChestNet DenseNet";

  return (
    <section className="cv-section" aria-labelledby="imaging-heading" id="chest-xray-viewer">
      <h2 className="cv-section-title" id="imaging-heading">Chest X-ray review</h2>
      <p className="cv-section-sub">
        The red box marks where the AI found the strongest abnormality. Use the heatmap overlay to compare intensity.
      </p>

      {imagingStatus && (
        <div className={`cv-imaging-status is-${imagingStatusTone(imagingStatus) || "neutral"}`}>
          <strong>Imaging status:</strong> {imagingStatus.replace(/_/g, " ")}
          <span> — {imagingStatusMessage(imagingStatus)}</span>
        </div>
      )}

      <div className="cv-imaging-proof">
        <h3 className="cv-imaging-proof-title">Analysis proof</h3>
        <div className="cv-imaging-proof-grid">
          <ProofRow label="Source file" value={fileName || "Uploaded image"} />
          <ProofRow label="Analysis engine" value={engineLabel} tone={isFallback ? "warn" : "ok"} />
          <ProofRow label="Model version" value={imaging.model_version || "—"} />
          <ProofRow
            label="TorchXRayVision installed"
            value={proof.txrv_installed ? "Yes" : "No — using fallback"}
            tone={proof.txrv_installed ? "ok" : "warn"}
          />
          <ProofRow
            label="Study status"
            value={imaging.status || proof.study_status || "—"}
          />
          <ProofRow
            label="Heatmap file"
            value={proof.heatmap_available ? "Generated on server" : "Not available"}
            tone={proof.heatmap_available ? "ok" : "warn"}
          />
          <ProofRow
            label="Source image loaded"
            value={sourceLoaded ? "Yes — visible below" : imaging.image_url ? "Loading…" : "No image URL"}
            tone={sourceLoaded ? "ok" : undefined}
          />
          <ProofRow
            label="Top finding"
            value={
              findings.length
                ? `${FINDING_LABELS[findings[0][0]] || findings[0][0]} — ${((findings[0][1].probability ?? 0) * 100).toFixed(1)}%`
                : "None scored"
            }
          />
          <ProofRow
            label="Flagged for review"
            value={detected.length ? detected.map(([k]) => FINDING_LABELS[k] || k).join(", ") : "None above threshold"}
            tone={detected.length ? "alert" : "ok"}
          />
          <ProofRow
            label="Imaging status"
            value={imagingStatus ? imagingStatus.replace(/_/g, " ") : "—"}
            tone={imagingStatusTone(imagingStatus)}
          />
          <ProofRow
            label="Marked disease area"
            value={regions.length ? `${regions.length} region(s) highlighted` : "No region returned"}
            tone={regions.length ? "ok" : "warn"}
          />
        </div>
        {isFallback && (
          <p className="cv-imaging-proof-note">
            Scores show <strong>12% placeholder values</strong> because the real ChestNet run failed
            (often a preprocessing error). Click <strong>Re-analyze X-ray</strong> below to run
            TorchXRayVision again, or upload the image once more.
          </p>
        )}
        {onReanalyze && (
          <div className="cv-imaging-reanalyze">
            <button
              type="button"
              className="cv-btn cv-btn-secondary"
              onClick={onReanalyze}
              disabled={reanalyzing}
            >
              {reanalyzing ? "Re-analyzing…" : "Re-analyze X-ray"}
            </button>
          </div>
        )}
      </div>

      <div className="cv-imaging-section">
        <div
          className="cv-imaging-viewport"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "center center",
            transition: "transform 200ms ease",
          }}
        >
          <div
            ref={stackRef}
            className="cv-imaging-stack"
            style={
              frameSize
                ? { width: `${frameSize.width}px`, height: `${frameSize.height}px` }
                : undefined
            }
          >
            <ClinicalBlobImage
              url={imaging.image_url}
              alt="Uploaded chest X-ray"
              className="cv-imaging-source"
              emptyMessage="Source X-ray could not be loaded from the server."
              onLoaded={() => {
                setSourceLoaded(true);
                setImageLoadFailed(false);
              }}
              onError={() => setImageLoadFailed(true)}
              onImageLayout={(img) => syncFrameFromImage(img)}
            />
            {imaging.heatmap_url && (
              <ClinicalBlobImage
                url={imaging.heatmap_url}
                alt="AI intensity overlay"
                className="cv-imaging-heatmap"
                emptyMessage=""
                style={{
                  opacity: showHeatmap ? heatmapOpacity / 100 : 0,
                  mixBlendMode: "screen",
                }}
              />
            )}
            {showRegions && regions.map((region, idx) => (
              <div
                key={`region-${idx}`}
                className="cv-imaging-region"
                style={{
                  left: `${(region.x || 0) * 100}%`,
                  top: `${(region.y || 0) * 100}%`,
                  width: `${(region.width || 0) * 100}%`,
                  height: `${(region.height || 0) * 100}%`,
                }}
                title={region.label || "Area to review"}
              >
                <span className="cv-imaging-region-tag">
                  {region.label || "Review this area"}
                </span>
                <span className="cv-imaging-region-corner cv-imaging-region-corner-tl" aria-hidden="true" />
                <span className="cv-imaging-region-corner cv-imaging-region-corner-tr" aria-hidden="true" />
                <span className="cv-imaging-region-corner cv-imaging-region-corner-bl" aria-hidden="true" />
                <span className="cv-imaging-region-corner cv-imaging-region-corner-br" aria-hidden="true" />
              </div>
            ))}
          </div>
        </div>

        <div className="cv-imaging-controls">
          <label className="cv-imaging-control">
            <span>Overlay strength</span>
            <input
              type="range"
              min={0}
              max={100}
              value={heatmapOpacity}
              onChange={(e) => setHeatmapOpacity(Number(e.target.value))}
              disabled={!showHeatmap || !imaging.heatmap_url}
            />
            <span>{heatmapOpacity}%</span>
          </label>
          <button
            type="button"
            className="cv-btn cv-btn-sm cv-btn-secondary"
            onClick={() => setShowHeatmap((v) => !v)}
            disabled={!imaging.heatmap_url}
          >
            {showHeatmap ? "Hide heatmap" : "Show heatmap"}
          </button>
          <button
            type="button"
            className={`cv-btn cv-btn-sm ${showRegions ? "cv-btn-primary" : "cv-btn-secondary"}`}
            onClick={() => setShowRegions((v) => !v)}
            disabled={!regions.length}
          >
            {showRegions ? "Hide anomaly box" : "Show anomaly box"}
          </button>
          <button
            type="button"
            className="cv-btn cv-btn-sm cv-btn-secondary"
            onClick={() => setZoom((z) => Math.min(z + 0.25, 3))}
          >
            Zoom in
          </button>
          <button
            type="button"
            className="cv-btn cv-btn-sm cv-btn-secondary"
            onClick={() => setZoom((z) => Math.max(z - 0.25, 0.5))}
          >
            Zoom out
          </button>
          <button type="button" className="cv-btn cv-btn-sm cv-btn-ghost" onClick={() => setZoom(1)}>
            Reset
          </button>
        </div>

        {regions.length > 0 && (
          <div className="cv-imaging-legend">
            <strong>Anomaly marker:</strong>{" "}
            {regions.map((r) => r.label).join(" · ")}
            <span className="cv-imaging-legend-note">
              Box is AI-assisted guidance only — confirm on the original film.
            </span>
          </div>
        )}
        {regions.length === 0 && detected.length > 0 && (
          <div className="cv-imaging-legend cv-imaging-legend-warn">
            <strong>No marker could be drawn for this saved case.</strong>
            <span className="cv-imaging-legend-note">
              Re-open after backend refresh, or re-upload the X-ray to regenerate the anomaly box.
            </span>
          </div>
        )}
      </div>

      <div style={{ marginTop: "var(--cv-space-3)" }}>
        <ImagingFindingsTable findings={imaging.findings || {}} />
      </div>
    </section>
  );
}
