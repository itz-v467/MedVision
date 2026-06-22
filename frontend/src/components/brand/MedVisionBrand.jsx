const LOGO_SRC = "/medvision-logo.png";
export const MEDVISION_TAGLINE = "intelligence that cares";

export function MedVisionBrand({ variant = "sidebar" }) {
  if (variant === "icon") {
    return (
      <span className="cv-brand cv-brand-icon" aria-hidden="true">
        <img src={LOGO_SRC} alt="" className="cv-brand-logo-icon" />
      </span>
    );
  }

  if (variant === "login") {
    return (
      <header className="cv-brand cv-brand-login">
        <div className="cv-brand-logo-wrap cv-brand-logo-wrap-login">
          <img src={LOGO_SRC} alt="MedVision" className="cv-brand-logo" />
        </div>
        <p className="cv-brand-tagline cv-brand-tagline-login">{MEDVISION_TAGLINE}</p>
      </header>
    );
  }

  if (variant === "compact") {
    return (
      <div className="cv-brand cv-brand-compact">
        <img src={LOGO_SRC} alt="MedVision" className="cv-brand-logo-compact" />
        <span className="cv-brand-tagline cv-brand-tagline-compact">{MEDVISION_TAGLINE}</span>
      </div>
    );
  }

  return (
    <div className="cv-brand cv-brand-sidebar">
      <div className="cv-brand-logo-wrap cv-brand-logo-wrap-sidebar">
        <img src={LOGO_SRC} alt="MedVision" className="cv-brand-logo" />
      </div>
      <span className="cv-brand-tagline cv-brand-tagline-sidebar">{MEDVISION_TAGLINE}</span>
    </div>
  );
}
