import { useState } from "react";
import { clinicalApi } from "../api/clinicalApi";
import { Messages } from "../enums/messages";

export function UploadPage() {
  const [file, setFile] = useState(null);
  const [fileType, setFileType] = useState("lab_report");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file) {
      setError("Please select a clinical file.");
      return;
    }
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("patient_external_id", "P-1001");
    formData.append("patient_name", "John Doe");
    formData.append("file_type", fileType);
    try {
      const data = await clinicalApi.upload(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <header className="page-header">
        <h2>Clinical AI Workflow</h2>
        <p>Upload → OCR/NLP/Imaging → Explainability → Summary → Review</p>
      </header>
      <form className="upload-panel" onSubmit={handleUpload}>
        <select value={fileType} onChange={(e) => setFileType(e.target.value)}>
          <option value="lab_report">Lab Report (PDF/CSV/TXT)</option>
          <option value="xray">Chest X-ray (PNG/JPG)</option>
          <option value="clinical_note">Clinical Note (TXT)</option>
        </select>
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt,.csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Run AI Pipeline"}
        </button>
      </form>
      {error ? <div className="error-banner">{error}</div> : null}
      {result ? (
        <div className="panel result-panel">
          <h3>{Messages.UPLOAD_SUCCESS}</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      ) : null}
    </div>
  );
}
