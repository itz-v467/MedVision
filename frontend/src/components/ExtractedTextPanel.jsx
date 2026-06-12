/**
 * Shows OCR raw text when labs are present or extraction partially succeeded.
 */
export function ExtractedTextPanel({ structuredData }) {
  if (!structuredData) return null;

  const text = structuredData.raw_text_preview || structuredData.raw_text || "";
  const method = structuredData.extraction_method;
  const chars = structuredData.chars_extracted ?? text.length;
  const biomarkerCount = structuredData.biomarkers?.length ?? 0;
  const engines = structuredData.ocr_engines_available;
  const warning = structuredData.extraction_warning;

  if (!text && !structuredData.extraction_warning) {
    return null;
  }

  return (
    <div className="extracted-text-panel">
      <div className="extracted-text-header">
        <h4>Extracted Report Text</h4>
        <div className="extracted-text-meta">
          {method && <span>Method: {method.replace(/_/g, " ")}</span>}
          {chars > 0 && <span>{chars} characters</span>}
          <span>{biomarkerCount} biomarkers parsed</span>
        </div>
      </div>
      {engines && (
        <div className="extracted-text-engines">
          OCR engines:{" "}
          {Object.entries(engines)
            .filter(([, ok]) => ok)
            .map(([name]) => name)
            .join(", ") || "none available — run pip install easyocr"}
        </div>
      )}
      {warning && !text && (
        <p className="extracted-text-empty">{warning}</p>
      )}
      {text ? (
        <pre className="extracted-text-body">{text}</pre>
      ) : !warning ? (
        <p className="extracted-text-empty">
          No readable text was extracted. Upload a new case after installing OCR (easyocr).
        </p>
      ) : null}
    </div>
  );
}
