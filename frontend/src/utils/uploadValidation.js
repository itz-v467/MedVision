const FILE_TYPE_MIME_MAP = {
  clinical_note: ["text/plain"],
  lab_report: ["application/pdf", "text/csv", "image/png", "image/jpeg"],
  xray: ["image/png", "image/jpeg"],
};

const EXTENSION_MIME_MAP = {
  ".txt": "text/plain",
  ".csv": "text/csv",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
};

const FILE_TYPE_LABELS = {
  clinical_note: "Clinical Note (TXT)",
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
  for (const [fileType, mimes] of Object.entries(FILE_TYPE_MIME_MAP)) {
    if (mimes.includes(mime)) {
      return fileType;
    }
  }
  return null;
}

export function validateUpload(file, fileType) {
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

  return { ok: true, mime };
}
