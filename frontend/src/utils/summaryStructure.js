/** Split dense clinical narrative into scannable sections (display only — no logic change). */

function splitSentences(text) {
  if (!text?.trim()) return [];
  const parts = text
    .replace(/\s+/g, " ")
    .trim()
    .split(/(?<=[.!?])\s+(?=[A-Z(])/);
  return parts.map((s) => s.trim()).filter(Boolean);
}

const KEYWORD_BUCKETS = {
  presentation: [
    "presenting", "complaint", "symptom", "year-old", "male", "female",
    "experiencing", "onset", "history", "reports", "patient",
  ],
  objective: [
    "x-ray", "chest", "imaging", "opacity", "scan", "radiolog",
    "demonstrates", "finding", "findings", "consistent with",
  ],
  laboratory: [
    "laboratory", "lab", "bilirubin", "ast", "alt", "wbc", "hemoglobin",
    "platelet", "elevated", "marker", "liver", "hepat", "cholest",
  ],
  impression: [
    "overall", "most consistent", "impression", "diagnosis", "suggest",
    "indicates", "prioritized", "consistent with", "likely", "suspicion",
  ],
  correlation: [
    "correlat", "pattern match", "reinforc", "multi-system", "concurrent",
    "secondary", "complication", "align", "link",
  ],
};

function scoreBucket(sentence, bucket) {
  const lower = sentence.toLowerCase();
  return KEYWORD_BUCKETS[bucket].reduce(
    (score, kw) => score + (lower.includes(kw) ? 1 : 0),
    0,
  );
}

function categorizeSentences(sentences, bucketKeys, labels, tones) {
  const buckets = bucketKeys.map((key) => ({ key, items: [] }));

  sentences.forEach((sentence) => {
    let bestIdx = 0;
    let bestScore = -1;
    bucketKeys.forEach((key, idx) => {
      const score = scoreBucket(sentence, key);
      if (score > bestScore) {
        bestScore = score;
        bestIdx = idx;
      }
    });
    if (bestScore === 0) {
      const emptyIdx = buckets.findIndex((b) => b.items.length === 0);
      buckets[emptyIdx >= 0 ? emptyIdx : buckets.length - 1].items.push(sentence);
    } else {
      buckets[bestIdx].items.push(sentence);
    }
  });

  return buckets
    .map((bucket, idx) => ({
      label: labels[idx] || "Notes",
      tone: tones[idx] || "neutral",
      bullets: bucket.items,
    }))
    .filter((section) => section.bullets.length > 0);
}

const PATIENT_CONFIG = {
  labels: ["Your situation", "What your tests showed", "What this may mean", "Additional notes"],
  tones: ["info", "warning", "success", "neutral"],
  buckets: ["presentation", "objective", "impression", "laboratory"],
};

const PHYSICIAN_CONFIG = {
  labels: ["Clinical presentation", "Imaging findings", "Laboratory results", "Working impression"],
  tones: ["clinical", "objective", "labs", "impression"],
  buckets: ["presentation", "objective", "laboratory", "impression"],
};

const CORRELATION_CONFIG = {
  labels: ["Symptom & imaging link", "Laboratory correlation", "Pattern analysis", "Clinical synthesis"],
  tones: ["info", "labs", "warning", "impression"],
  buckets: ["correlation", "laboratory", "objective", "impression"],
};

const RATIONALE_CONFIG = {
  labels: ["Key evidence", "Clinical reasoning", "Priority & context"],
  tones: ["info", "clinical", "success"],
  buckets: ["objective", "impression", "presentation"],
};

/**
 * @param {string} text
 * @param {"patient"|"physician"|"correlation"|"rationale"} variant
 */
export function buildSummarySections(text, variant = "patient") {
  const sentences = splitSentences(text);
  if (!sentences.length) return [];

  const config =
    variant === "physician" ? PHYSICIAN_CONFIG
    : variant === "correlation" ? CORRELATION_CONFIG
    : variant === "rationale" ? RATIONALE_CONFIG
    : PATIENT_CONFIG;

  if (sentences.length <= 2 && variant === "patient") {
    return sentences.map((sentence, idx) => ({
      label: config.labels[Math.min(idx, config.labels.length - 1)],
      tone: config.tones[Math.min(idx, config.tones.length - 1)],
      bullets: [sentence],
    }));
  }

  return categorizeSentences(
    sentences,
    config.buckets,
    config.labels,
    config.tones,
  );
}
