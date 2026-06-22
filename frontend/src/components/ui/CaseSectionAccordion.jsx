import { useState } from "react";
import { ClinicalTabs } from "./ClinicalTabs";

export function CaseSectionAccordion({ sections, defaultOpenIds = [] }) {
  const [openIds, setOpenIds] = useState(() => new Set(defaultOpenIds));

  const toggle = (id) => {
    setOpenIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="cv-case-accordion">
      {sections.map((section) => {
        const isOpen = openIds.has(section.id);
        return (
          <section key={section.id} className="cv-case-accordion-item">
            <button
              type="button"
              className={`cv-case-accordion-trigger${isOpen ? " is-open" : ""}`}
              aria-expanded={isOpen}
              onClick={() => toggle(section.id)}
            >
              <span>{section.title}</span>
              {section.badge && <span className="cv-case-accordion-badge">{section.badge}</span>}
              <span className="cv-case-accordion-chevron" aria-hidden="true">{isOpen ? "−" : "+"}</span>
            </button>
            {isOpen && <div className="cv-case-accordion-panel">{section.content}</div>}
          </section>
        );
      })}
    </div>
  );
}

export { ClinicalTabs };
