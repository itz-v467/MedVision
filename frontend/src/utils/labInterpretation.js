/** Client-side reference ranges + normalization (mirrors backend) for legacy records. */
const RANGES = {
  Hemoglobin: { low: 12, high: 16, unit: "g/dL" },
  Glucose: { low: 70, high: 100, unit: "mg/dL" },
  WBC: { low: 4.5, high: 11, unit: "10^3/uL", cellCount: true },
  RBC: { low: 4.2, high: 5.8, unit: "10^6/uL" },
  Platelets: { low: 150, high: 400, unit: "10^3/uL", cellCount: true },
  Hematocrit: { low: 36, high: 46, unit: "%" },
  Creatinine: { low: 0.7, high: 1.3, unit: "mg/dL" },
  Urea: { low: 15, high: 40, unit: "mg/dL" },
  ALT: { low: 7, high: 56, unit: "U/L" },
  AST: { low: 10, high: 40, unit: "U/L" },
  LDL: { low: 0, high: 130, unit: "mg/dL", highOnly: true },
  HDL: { low: 40, high: 999, unit: "mg/dL", lowOnly: true },
  Triglycerides: { low: 0, high: 150, unit: "mg/dL", highOnly: true },
  Cholesterol: { low: 0, high: 200, unit: "mg/dL", highOnly: true },
  TSH: { low: 0.4, high: 4.0, unit: "mIU/L" },
};

function normalizeValue(name, value) {
  const ref = RANGES[name];
  let v = Number(value);
  if (!ref) return { value: v, unit: "" };

  if (ref.cellCount && v >= 10000) {
    v = v / 1000;
  } else if (ref.cellCount && v > ref.high * 10 && v < 10000) {
    const scaled = v / 1000;
    if (scaled >= ref.low && scaled <= ref.high) v = scaled;
  }

  return { value: v, unit: ref.unit };
}

function classifyLegacy(name, value) {
  const norm = normalizeValue(name, value);
  const ref = RANGES[name];
  const v = norm.value;
  if (!ref) {
    return { status: "unknown", flag: "N/A", is_abnormal: false, reference_range: "—", interpretation: "" };
  }
  const rangeText = `${ref.low}–${ref.high} ${ref.unit}`;
  let isAbnormal = false;
  let flag = "NORMAL";
  let interpretation = `Within reference range (${rangeText})`;

  if (ref.highOnly && v > ref.high) {
    isAbnormal = true;
    flag = "HIGH";
    interpretation = `Above desirable limit (${v} > ${ref.high} ${ref.unit})`;
  } else if (ref.lowOnly && v < ref.low) {
    isAbnormal = true;
    flag = "LOW";
    interpretation = `Below desirable level (${v} < ${ref.low} ${ref.unit})`;
  } else if (!ref.highOnly && !ref.lowOnly) {
    if (v < ref.low) {
      isAbnormal = true;
      flag = "LOW";
      interpretation = `Below reference range (${v} < ${ref.low} ${ref.unit})`;
    } else if (v > ref.high) {
      isAbnormal = true;
      flag = "HIGH";
      interpretation = `Above reference range (${v} > ${ref.high} ${ref.unit})`;
    }
  }

  return {
    status: isAbnormal ? "abnormal" : "normal",
    flag,
    is_abnormal: isAbnormal,
    reference_range: rangeText,
    interpretation,
    display_value: `${v} ${ref.unit}`,
    value: v,
    unit: ref.unit,
  };
}

export function enrichBiomarkers(biomarkers = []) {
  return biomarkers.map((item) => {
    if (item.status && item.reference_range && item.display_value) {
      return item;
    }
    const legacy = classifyLegacy(item.name, Number(item.value));
    return {
      ...item,
      ...legacy,
      raw_value: item.raw_value ?? item.value,
    };
  });
}
