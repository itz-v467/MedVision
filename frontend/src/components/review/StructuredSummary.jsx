import { buildSummarySections } from "../../utils/summaryStructure";

const TONE_ICONS = {
  info: "◆",
  warning: "▲",
  success: "●",
  clinical: "✦",
  objective: "◎",
  labs: "◈",
  impression: "✓",
  neutral: "—",
};

/**
 * Renders a long clinical paragraph as color-coded, labeled bullet sections.
 * Content is unchanged — only layout and grouping.
 */
export function StructuredSummary({ text, variant = "patient", title }) {
  const cleaned = (text || "")
    .replace(/^\*\*Cross-modal correlation:\*\*\s*/i, "")
    .replace(/^Cross-modal correlation:\s*/i, "")
    .trim();
  const sections = buildSummarySections(cleaned, variant);
  if (!sections.length) return null;

  return (
    <div className={`cv-structured-summary is-${variant}`}>
      {title && <h4 className="cv-structured-summary-title">{title}</h4>}
      <div className="cv-structured-summary-grid">
        {sections.map((section) => (
          <article
            key={`${section.label}-${section.bullets[0]?.slice(0, 24)}`}
            className={`cv-summary-block cv-summary-block--${section.tone}`}
          >
            <header className="cv-summary-block-head">
              <span className="cv-summary-block-icon" aria-hidden="true">
                {TONE_ICONS[section.tone] || "•"}
              </span>
              <span className="cv-summary-block-label">{section.label}</span>
            </header>
            <ul className="cv-summary-block-list">
              {section.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  );
}
