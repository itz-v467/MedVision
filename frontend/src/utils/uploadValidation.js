const EXTENSION_MIME_MAP = {
  ".txt": "text/plain",
  ".csv": "text/csv",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
};

const FILE_TYPE_MIME_MAP = {
  lab_report: ["application/pdf", "text/csv", "image/png", "image/jpeg"],
  xray: ["image/png", "image/jpeg"],
};

const IMAGING_NAME_HINTS = /xray|x-?ray|chest|thorax|pneu|pna|lung|radiograph|cxr|scan/i;
const LAB_NAME_HINTS = /lab|blood|cbc|panel|pathology|metabolic|hemoglobin|glucose/i;

const FILE_TYPE_LABELS = {
  lab_report: "Lab Report (PDF / CSV / Photo)",
  xray: "Chest X-Ray (PNG / JPG)",
};

function extensionOf(fileName) {
  const dot = fileName.lastIndexOf(".");
  return dot >= 0 ? fileName.slice(dot).toLowerCase() : "";
}

export function resolveMimeType(file) {
  if (file.type && file.type !== "application/octet-stream") {
    return file.type;
  }
  return EXTENSION_MIME_MAP[extensionOf(file.name)] || file.type || "";
}

export function suggestFileType(file) {
  const mime = resolveMimeType(file);
  const name = file.name || "";

  if (mime === "text/plain") return null;
  if (mime === "application/pdf" || mime === "text/csv") return "lab_report";
  if (mime === "image/png" || mime === "image/jpeg") {
    if (IMAGING_NAME_HINTS.test(name)) return "xray";
    if (LAB_NAME_HINTS.test(name)) return "lab_report";
    return "xray";
  }
  return null;
}

export function fileTypeLabel(fileType) {
  return FILE_TYPE_LABELS[fileType] || fileType;
}

export function validateUpload(file, fileType) {
  if (!fileType) {
    return {
      ok: false,
      message: "Please select a document type before uploading.",
    };
  }

  const mime = resolveMimeType(file);
  const allowed = FILE_TYPE_MIME_MAP[fileType];

  if (!allowed) {
    return { ok: false, message: "Unknown document type selected." };
  }

  if (!mime) {
    return {
      ok: false,
      message: "Could not determine file type. Use PDF, PNG, JPG, TXT, or CSV.",
    };
  }

  if (!allowed.includes(mime)) {
    const selected = FILE_TYPE_LABELS[fileType];
    const suggested = suggestFileType(file);
    const hint = suggested
      ? ` Try "${FILE_TYPE_LABELS[suggested]}" instead.`
      : "";
    return {
      ok: false,
      message: `“${file.name}” does not match ${selected}.${hint}`,
      suggestedFileType: suggested,
    };
  }

  const name = file.name || "";
  if ((mime === "image/png" || mime === "image/jpeg") && fileType === "xray" && LAB_NAME_HINTS.test(name)) {
    return {
      ok: false,
      message:
        "This looks like a lab/blood report image, not a chest X-ray. Select Lab Report or upload the chest scan.",
    };
  }
  if ((mime === "image/png" || mime === "image/jpeg") && fileType === "lab_report" && IMAGING_NAME_HINTS.test(name)) {
    return {
      ok: false,
      message:
        "This looks like a chest X-ray image, not a lab report. Select Chest X-Ray for proper analysis.",
    };
  }

  return { ok: true, mime };
}

function sampleImagePixels(imageData) {
  const { data, width, height } = imageData;
  const step = Math.max(1, Math.floor((width * height) / 4000));
  const chroma = [];
  const luminance = [];
  for (let i = 0; i < width * height; i += step) {
    const offset = i * 4;
    const red = data[offset];
    const green = data[offset + 1];
    const blue = data[offset + 2];
    chroma.push(Math.max(red, green, blue) - Math.min(red, green, blue));
    luminance.push(0.299 * red + 0.587 * green + 0.114 * blue);
  }
  return { chroma, luminance };
}

function mean(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function classifyPixels({ chroma, luminance }) {
  if (!chroma.length) return "unknown";

  const avgChroma = mean(chroma);
  const lumStd = Math.sqrt(
    mean(luminance.map((value) => (value - mean(luminance)) ** 2))
  );
  const whiteRatio = luminance.filter((value) => value > 235).length / luminance.length;
  const midRatio = luminance.filter((value) => value > 40 && value < 200).length / luminance.length;

  if (whiteRatio > 0.32 && avgChroma > 16) return "lab_report";
  if (avgChroma < 22 && midRatio > 0.22 && lumStd > 22) return "xray";
  if (avgChroma < 14) return "xray";
  if (whiteRatio > 0.45 && avgChroma > 10) return "lab_report";
  return "unknown";
}

export async function classifyImageFile(file) {
  const mime = resolveMimeType(file);
  if (mime !== "image/png" && mime !== "image/jpeg") {
    return "unknown";
  }

  try {
    const bitmap = await createImageBitmap(file);
    const canvas = document.createElement("canvas");
    const maxSide = 256;
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const ctx = canvas.getContext("2d");
    if (!ctx) return "unknown";
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();
    const stats = sampleImagePixels(ctx.getImageData(0, 0, canvas.width, canvas.height));
    return classifyPixels(stats);
  } catch {
    return "unknown";
  }
}

export async function validateImageContent(file, fileType) {
  const mime = resolveMimeType(file);
  if (mime !== "image/png" && mime !== "image/jpeg") {
    return { ok: true };
  }
  if (fileType !== "xray" && fileType !== "lab_report") {
    return { ok: true };
  }

  const detected = await classifyImageFile(file);
  if (detected === "unknown") {
    return { ok: true };
  }

  if (fileType === "xray" && detected === "lab_report") {
    return {
      ok: false,
      message:
        "This image looks like a lab/blood report photo, not a chest X-ray. Select Lab Report or upload a chest scan.",
    };
  }

  if (fileType === "lab_report" && detected === "xray") {
    return {
      ok: false,
      message:
        "This image looks like a chest X-ray, not a lab report. Select Chest X-Ray for proper analysis.",
    };
  }

  return { ok: true };
}
