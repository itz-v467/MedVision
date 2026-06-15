/** Clinical + plain-language evidence trail for physicians and patients. */

const TERM_CATEGORIES = {
  diseases: "Conditions identified",
  symptoms: "Symptoms identified",
  medications: "Medications mentioned",
  allergies: "Allergies mentioned",
};

const FINDING_COPY = {
  pneumothorax: {
    clinical: "Pneumothorax",
    plain: "Air trapped between the lung and chest wall — can cause lung collapse.",
  },
  opacity: {
    clinical: "Lung opacity / consolidation",
    plain: "A dense or cloudy area in the lung — may suggest pneumonia or infection.",
  },
  pleural_effusion: {
    clinical: "Pleural effusion",
    plain: "Fluid around the lung — may need further imaging or drainage evaluation.",
  },
  nodule: {
    clinical: "Pulmonary nodule",
    plain: "A small spot in the lung — often needs follow-up to rule out malignancy.",
  },
  cardiomegaly: {
    clinical: "Cardiomegaly",
    plain: "Enlarged heart silhouette on the film — correlate with cardiac history.",
  },
};

const DOC_TYPE_LABELS = {
  xray: "Chest X-ray",
  lab_report: "Laboratory report",
  clinical_note: "Clinical note",
};

function pct(score) {
  return Math.round((score ?? 0) * 100);
}

function confidenceLabel(score) {
  const value = pct(score);
  if (value >= 80) return `High confidence (${value}%)`;
  if (value >= 55) return `Moderate confidence (${value}%)`;
  if (value > 0) return `Low confidence (${value}%) — verify against source`;
  return "Confidence not measured";
}

function cleanExcerpt(text, maxLen = 500) {
  if (!text) return "";
  let normalized = text
    .replace(/\r\n/g, "\n")
    .replace(/[^\S\n]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  const lines = normalized.split("\n").filter((line) => {
    const s = line.trim();
    if (s.length < 4) return false;
    const letters = (s.match(/[a-zA-Z]/g) || []).length;
    const ratio = letters / Math.max(s.length, 1);
    return ratio > 0.25 || /patient|report|hospital|test|blood|lab|age|gender|id/i.test(s);
  });

  let excerpt = (lines.length ? lines : normalized.split("\n")).slice(0, 14).join("\n").trim();
  if (excerpt.length > maxLen) excerpt = `${excerpt.slice(0, maxLen).trim()}…`;
  return excerpt;
}

function extractPatientLine(text) {
  if (!text) return null;
  const match = text.match(/patient[^:\n]*[:\-]\s*([^\n]+)/i);
  if (!match) return null;
  return match[1].replace(/\s+/g, " ").trim().slice(0, 80);
}

function formatBiomarkerRows(biomarkers = []) {
  return biomarkers.slice(0, 8).map((b) => ({
    label: b.display_name || b.name || b.test_name || "Test",
    value: [b.value, b.unit].filter(Boolean).join(" ") || "—",
    note: b.flag && b.flag !== "NORMAL" ? `Flag: ${b.flag}` : b.reference_range ? `Ref: ${b.reference_range}` : "",
    tone: b.flag && b.flag !== "NORMAL" ? "alert" : undefined,
  }));
}

function formatTermsList(entities) {
  if (!entities || typeof entities !== "object" || Array.isArray(entities)) return [];
  return Object.entries(entities)
    .filter(([, values]) => Array.isArray(values) && values.length > 0)
    .map(([key, values]) => ({
      label: TERM_CATEGORIES[key] || key.replace(/_/g, " "),
      items: values,
    }));
}

function formatImagingFindingRows(findings) {
  if (!findings || typeof findings !== "object") return [];
  return Object.entries(findings)
    .filter(([key]) => !key.startsWith("_"))
    .sort((a, b) => (b[1]?.probability ?? 0) - (a[1]?.probability ?? 0))
    .map(([key, data]) => {
      const copy = FINDING_COPY[key] || {
        clinical: key.replace(/_/g, " "),
        plain: "AI-detected pattern on the chest film.",
      };
      const probability = pct(data?.probability ?? 0);
      const flagged = data?.detected || probability >= 40;
      return {
        label: copy.clinical,
        value: `${probability}% AI probability`,
        note: flagged
          ? `${copy.plain} Flagged for physician review.`
          : `${copy.plain} Below alert threshold — still confirm clinically.`,
        tone: flagged ? "alert" : undefined,
      };
    });
}

function chunkText(chunk) {
  return (
    chunk?.chunk_text ||
    chunk?.text ||
    chunk?.content ||
    chunk?.snippet ||
    chunk?.page_content ||
    (typeof chunk === "string" ? chunk : "")
  );
}

function summarizeParsedContext(parsed) {
  const cards = [];
  const docType = parsed?.file_type;
  if (docType) {
    cards.push({
      label: "Record type",
      value: DOC_TYPE_LABELS[docType] || docType,
      note: "Used to choose the correct analysis pipeline.",
    });
  }

  const biomarkers = parsed?.ocr?.structured_data?.biomarkers || [];
  if (biomarkers.length) {
    cards.push({
      label: "Lab values extracted",
      value: `${biomarkers.length} result(s)`,
      note: biomarkers
        .slice(0, 3)
        .map((b) => `${b.display_name || b.name}: ${b.value || "—"} ${b.unit || ""}`.trim())
        .join(" · "),
    });
  }

  const imagingFindings = parsed?.imaging?.findings;
  if (imagingFindings && typeof imagingFindings === "object") {
    const top = formatImagingFindingRows(imagingFindings).slice(0, 3);
    if (top.length) {
      cards.push({
        label: "Imaging signals used",
        value: top.map((row) => row.label).join(", "),
        note: top.map((row) => `${row.label} — ${row.value}`).join(" · "),
        tone: top.some((row) => row.tone === "alert") ? "alert" : undefined,
      });
    }
  }

  const entities = parsed?.nlp?.entities;
  if (entities && typeof entities === "object") {
    const diseases = entities.diseases || [];
    const symptoms = entities.symptoms || [];
    if (diseases.length || symptoms.length) {
      cards.push({
        label: "Clinical terms linked",
        value: [...diseases, ...symptoms].slice(0, 4).join(", "),
        note: "Matched to standard medical terminology for the summary.",
      });
    }
  }

  const correlation = parsed?.correlation?.confidence ?? parsed?.correlation?.score;
  if (typeof correlation === "number" && correlation > 0) {
    cards.push({
      label: "Cross-source agreement",
      value: `${pct(correlation)}%`,
      note: "How closely document text, terms, and imaging aligned.",
    });
  }

  return cards;
}

function humanizeRagChunk(chunk) {
  const raw = String(chunkText(chunk) || "").trim();
  if (!raw) return null;

  if (raw.startsWith("{") || raw.startsWith("[")) {
    try {
      const parsed = JSON.parse(raw);
      const cards = summarizeParsedContext(parsed);
      if (cards.length) return { cards, sourceType: chunk?.source_type };
    } catch {
      /* fall through to excerpt */
    }
  }

  const excerpt = cleanExcerpt(raw, 280);
  if (!excerpt) return null;
  return {
    excerpt,
    sourceType: chunk?.source_type,
    similarity: chunk?.similarity,
  };
}

function sourceTypeLabel(sourceType) {
  const map = {
    workflow: "Full case context",
    ocr: "Document text",
    ocr_text: "Document text",
    imaging: "Imaging analysis",
    nlp: "Clinical terminology",
  };
  return map[sourceType] || "Case information";
}

function buildDocumentSource(detail) {
  const manifest = detail?.document_manifest?.length
    ? detail.document_manifest
    : (detail?.documents || []).map((doc) => ({
        file_type: doc.file_type,
        file_name: doc.file_name,
      }));
  const caseType = detail?.encounter?.case_type || detail?.correlation?.case_type || "";
  const docType = manifest[0]?.file_type || detail?.documents?.[0]?.file_type || "";
  const ocrData = detail?.ocr?.structured_data;
  if (!ocrData || !Object.keys(ocrData).length) return null;

  if (caseType === "multimodal" && manifest.length > 1) {
    const cards = manifest.map((doc) => ({
      label: DOC_TYPE_LABELS[doc.file_type] || doc.file_type,
      value: doc.file_name || "Uploaded file",
      note:
        doc.file_type === "lab_report" && typeof doc.biomarker_count === "number"
          ? `${doc.biomarker_count} lab value(s) extracted`
          : doc.file_type === "xray"
            ? "Chest imaging AI pipeline applied"
            : "Text extracted for clinical terms",
    }));
    return {
      id: "ocr",
      title: "Documents reviewed",
      summary: `${manifest.length} files in one unified case`,
      detailTitle: "Per-document intake manifest",
      intro:
        "Each document was validated, stored, and processed with the appropriate pipeline before fusion.",
      cards,
    };
  }

  const preview = ocrData.raw_text_preview || ocrData.raw_text || "";
  const biomarkers = ocrData.biomarkers || [];
  const patientLine = extractPatientLine(preview);
  const isXray = docType === "xray";

  if (isXray) {
    const cards = [
      {
        label: "Document type",
        value: "Chest X-ray image",
        note: "Blood panel parsing is not applied to radiographs.",
      },
      {
        label: "Text extraction",
        value: confidenceLabel(detail.ocr?.confidence),
        note: ocrData.extraction_warning || "Limited text is expected on X-ray images.",
      },
    ];
    if (patientLine) {
      cards.unshift({
        label: "Name on image (if readable)",
        value: patientLine,
        note: "Compare with the patient entered at upload.",
      });
    }
    return {
      id: "ocr",
      title: "Document reviewed",
      summary: "Chest X-ray — no lab values expected",
      detailTitle: "What we extracted from the upload",
      intro:
        "The file was read for any visible labels or text. The main diagnosis support comes from imaging AI below.",
      cards,
    };
  }

  const rows = formatBiomarkerRows(biomarkers);
  const highlights = [];
  if (patientLine) highlights.push(`Patient name on report: ${patientLine}`);
  if (biomarkers.length) {
    highlights.push(`${biomarkers.length} laboratory value(s) identified`);
  }

  return {
    id: "ocr",
    title: "Document reviewed",
    summary:
      biomarkers.length > 0
        ? `${biomarkers.length} lab value${biomarkers.length === 1 ? "" : "s"} extracted`
        : confidenceLabel(detail.ocr?.confidence),
    detailTitle: "Laboratory & report extraction",
    intro:
      "Text was extracted from the uploaded report. Values below were used to build the summary.",
    highlights,
    rows,
    excerpt: cleanExcerpt(preview),
    excerptNote:
      "Quoted text from your file. Always verify against the original report before clinical decisions.",
    confidenceNote: confidenceLabel(detail.ocr?.confidence),
  };
}

function buildTermsSource(detail) {
  const entities = detail?.nlp?.entities;
  if (!entities) return null;

  const terms = formatTermsList(entities);
  const count = terms.reduce((n, t) => n + t.items.length, 0);
  if (!count) return null;

  const icd = detail?.nlp?.icd10_codes || [];
  const snomed = detail?.nlp?.snomed_codes || [];
  const cards = [];
  if (icd.length) {
    cards.push({
      label: "ICD-10 codes suggested",
      value: icd.slice(0, 4).join(", "),
      note: "Diagnosis codes mapped from terms in the document.",
    });
  }
  if (snomed.length) {
    cards.push({
      label: "SNOMED CT concepts",
      value: snomed.slice(0, 4).join(", "),
      note: "Standard clinical concepts for interoperability.",
    });
  }

  return {
    id: "nlp",
    title: "Medical terms mapped",
    summary: `${count} term${count === 1 ? "" : "s"} · ICD-10 / SNOMED when matched`,
    detailTitle: "Clinical language found in the record",
    intro:
      "These terms were identified in the document and linked to standard medical vocabulary.",
    terms,
    cards,
  };
}

function buildImagingSource(detail) {
  if (!detail?.imaging || detail.imaging.skipped) return null;
  const findings = detail.imaging.findings;
  if (!findings || !Object.keys(findings).length) return null;

  const rows = formatImagingFindingRows(findings);
  const flagged = rows.filter((row) => row.tone === "alert");
  const regions = Array.isArray(detail.imaging.regions) ? detail.imaging.regions : [];
  const cards = [
    {
      label: "Analysis model",
      value: detail.imaging.model_version || "—",
      note: detail.imaging.proof?.is_fallback
        ? "Fallback scorer active — install TorchXRayVision for full ChestNet."
        : "TorchXRayVision chest pathology model.",
    },
    {
      label: "Overall imaging confidence",
      value: confidenceLabel(detail.imaging.confidence),
      note: "Based on the highest pathology probability returned.",
    },
  ];
  if (regions.length) {
    cards.push({
      label: "Marked region on scan",
      value: regions[0].label || "Anomaly box drawn on image below",
      note: "Scroll to the chest X-ray viewer to see the highlighted area.",
      tone: "alert",
    });
  }

  return {
    id: "imaging",
    title: "Chest X-ray analyzed",
    summary: flagged.length
      ? `${flagged.length} finding${flagged.length === 1 ? "" : "s"} flagged`
      : `${rows.length} pattern${rows.length === 1 ? "" : "s"} scored`,
    detailTitle: "Imaging AI findings (for physician review)",
    intro:
      "The scan was screened for common chest pathologies. This does not replace a radiologist's read.",
    rows,
    cards,
    highlights: flagged.slice(0, 3).map((row) => `${row.label}: ${row.value}`),
  };
}

function buildCorrelationSource(detail) {
  const correlation = detail?.correlation;
  const cards = correlation?.cards;
  if (!cards?.length) return null;

  return {
    id: "correlation",
    title: "Cross-check & correlation",
    summary: `${cards.length} lab↔imaging link${cards.length === 1 ? "" : "s"} for review`,
    detailTitle: "Automated cross-modal correlation",
    intro:
      "These plain-language links connect laboratory signals with chest imaging findings. Physician confirmation is required.",
    cards: cards.map((card) => ({
      label: card.label,
      value: card.value,
      note: card.note,
      tone: card.tone,
    })),
    highlights: cards.map((card) => `${card.label}: ${card.value}`),
  };
}

function buildReferencesSource(detail) {
  const evidenceBundle = detail?.summary?.evidence_sources;
  if (!evidenceBundle || typeof evidenceBundle !== "object") return null;

  const ragChunks = Array.isArray(evidenceBundle.rag_chunks) ? evidenceBundle.rag_chunks : [];
  if (!ragChunks.length) return null;

  const cards = [];
  const references = [];

  ragChunks.slice(0, 5).forEach((chunk, idx) => {
    const human = humanizeRagChunk(chunk);
    if (!human) return;

    if (human.cards?.length) {
      human.cards.forEach((card) => {
        if (!cards.some((c) => c.label === card.label && c.value === card.value)) {
          cards.push(card);
        }
      });
      references.push(
        `${sourceTypeLabel(human.sourceType)} — ${human.cards.map((c) => c.label).join(", ")}`
      );
      return;
    }

    if (human.excerpt) {
      const sim = human.similarity ? ` (${pct(human.similarity)}% match)` : "";
      references.push(`${sourceTypeLabel(human.sourceType)}${sim}: ${human.excerpt}`);
    } else {
      references.push(`Source ${idx + 1} from ${sourceTypeLabel(chunk?.source_type)}`);
    }
  });

  if (!cards.length && !references.length) return null;

  return {
    id: "rag",
    title: "Summary cross-check",
    summary: `${ragChunks.length} internal reference${ragChunks.length === 1 ? "" : "s"} used`,
    detailTitle: "Facts combined before writing the summary",
    intro:
      "The AI summary was grounded on these case facts — not on external web sources.",
    cards,
    references,
  };
}

/** Build clinical evidence steps for the review page. */
export function buildEvidenceSources(detail) {
  const builders = [
    buildDocumentSource,
    buildTermsSource,
    buildImagingSource,
    buildCorrelationSource,
    buildReferencesSource,
  ];
  const sources = builders.map((fn) => fn(detail)).filter(Boolean);

  return sources.map((source, idx) => ({
    ...source,
    step: idx + 1,
  }));
}

export { FINDING_COPY, formatImagingFindingRows };
