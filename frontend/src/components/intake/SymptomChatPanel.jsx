import { useCallback, useEffect, useRef, useState } from "react";
import { clinicalApi } from "../../api/clinicalApi";

const WELCOME = {
  role: "assistant",
  message_text:
    "Tell me what symptoms you're experiencing — when they started, how severe they are, and anything that makes them better or worse. I'll help organize this for your doctor.",
};

const RISK_LABELS = {
  low: "Low urgency",
  moderate: "Moderate urgency",
  high: "High urgency",
  emergency: "Emergency — seek care now",
};

export function SymptomChatPanel({
  messages,
  onMessagesChange,
  assessment,
  onAssessmentChange,
  assistantMode,
  onAssistantModeChange,
  patientName,
  patientAge,
  patientGender,
  disabled = false,
}) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!messages.length) {
      onMessagesChange([WELCOME]);
    }
  }, [messages.length, onMessagesChange]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading || disabled) return;

    setLoading(true);
    setError("");
    setInput("");

    const optimistic = [...messages, { role: "patient", message_text: text }];
    onMessagesChange(optimistic);

    try {
      const data = await clinicalApi.triageConverse({
        message: text,
        messages,
        patient_name: patientName,
        patient_age: patientAge,
        patient_gender: patientGender,
      });
      onMessagesChange(data.messages || optimistic);
      if (onAssessmentChange && data.assessment) {
        onAssessmentChange(data.assessment);
      }
      if (onAssistantModeChange && data.assistant_mode) {
        onAssistantModeChange(data.assistant_mode, data.llm_configured);
      }
    } catch (err) {
      setError(err.message || "Could not reach symptom assistant.");
      onMessagesChange(messages);
    } finally {
      setLoading(false);
    }
  }, [
    input,
    loading,
    disabled,
    messages,
    onMessagesChange,
    onAssessmentChange,
    onAssistantModeChange,
    patientName,
    patientAge,
    patientGender,
  ]);

  const patientTurns = messages.filter((m) => m.role === "patient").length;
  const riskLevel = assessment?.risk_level;
  const modeLabel =
    assistantMode === "openai"
      ? "AI assistant (OpenAI)"
      : assistantMode === "gemini"
        ? "AI assistant (Gemini)"
        : assistantMode === "guided"
          ? "Guided intake"
          : null;

  return (
    <div className="cv-symptom-chat">
      <div className="cv-symptom-chat-head">
        <div className="cv-symptom-chat-head-row">
          <div>
            <h4>Symptom assistant</h4>
            <p>Triage guidance only — not a diagnosis. Your doctor reviews everything.</p>
            {modeLabel && (
              <span className="cv-symptom-chat-mode">{modeLabel}</span>
            )}
          </div>
          {riskLevel && (
            <span className={`cv-triage-risk-chip is-${riskLevel}`}>
              {RISK_LABELS[riskLevel] || riskLevel}
            </span>
          )}
        </div>
        {assessment?.recommended_disposition && (
          <p className="cv-symptom-chat-disposition">{assessment.recommended_disposition}</p>
        )}
        {assessment?.escalation_required && (
          <p className="cv-symptom-chat-escalation" role="alert">
            Possible emergency symptoms detected. Seek urgent medical care if you feel unsafe.
          </p>
        )}
        {(assessment?.missing_factors?.length > 0 || assessment?.data_completeness < 0.7) && (
          <p className="cv-symptom-chat-missing">
            To give your doctor a clearer picture, please also share:{" "}
            {(assessment.missing_factors || [])
              .map((f) => f.replace(/_/g, " "))
              .join(", ") || "more symptom details"}
          </p>
        )}
      </div>

      <div className="cv-symptom-chat-thread" ref={scrollRef} aria-live="polite">
        {messages.map((msg, idx) => (
          <div
            key={`msg-${idx}`}
            className={`cv-symptom-chat-bubble is-${msg.role === "patient" ? "patient" : "assistant"}`}
          >
            <span className="cv-symptom-chat-role">
              {msg.role === "patient" ? "You" : "Assistant"}
            </span>
            <p>{msg.message_text}</p>
          </div>
        ))}
        {loading && <div className="cv-symptom-chat-typing">Assistant is thinking…</div>}
      </div>

      {patientTurns > 0 && (
        <p className="cv-symptom-chat-status">
          {patientTurns} symptom message{patientTurns === 1 ? "" : "s"} captured for this case.
        </p>
      )}

      {error && <p className="cv-symptom-chat-error">{error}</p>}

      <div className="cv-symptom-chat-input-row">
        <input
          type="text"
          className="cv-symptom-chat-input"
          placeholder="e.g. fever and cough for 3 days…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), sendMessage())}
          disabled={disabled || loading}
          aria-label="Symptom message"
        />
        <button
          type="button"
          className="cv-btn cv-btn-primary cv-btn-sm"
          onClick={sendMessage}
          disabled={disabled || loading || !input.trim()}
        >
          Send
        </button>
      </div>

      <p className="cv-symptom-chat-disclaimer">
        Informational triage only. A licensed physician must review before any clinical decision.
      </p>
    </div>
  );
}
