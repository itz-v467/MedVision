import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clinicalApi } from "../../api/clinicalApi";
import { AppRoutes } from "../../enums/routes";

/** Always-visible sidebar search — plain language for doctors & staff. */
export function SidebarPatientSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef(null);

  const runSearch = useCallback(async (text) => {
    const q = text.trim();
    if (q.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await clinicalApi.searchPatients(q, 6);
      setResults(data.patients || []);
      setOpen(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim().length >= 2) {
        runSearch(query);
      } else {
        setResults([]);
        setOpen(false);
      }
    }, 320);
    return () => clearTimeout(timer);
  }, [query, runSearch]);

  useEffect(() => {
    const onClickOutside = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const openPatient = (patient) => {
    setOpen(false);
    setQuery("");
    navigate(`${AppRoutes.ENCOUNTERS}?q=${encodeURIComponent(patient.external_id)}`);
  };

  return (
    <div className="mv-sidebar-search" ref={wrapRef}>
      <label className="mv-sidebar-search-label" htmlFor="sidebar-patient-search">
        Find a patient
      </label>
      <div className="mv-sidebar-search-field">
        <span className="mv-sidebar-search-icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3-3" />
          </svg>
        </span>
        <input
          id="sidebar-patient-search"
          type="search"
          placeholder="Name or MV number…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          autoComplete="off"
        />
        {loading && <span className="mv-sidebar-search-spinner" aria-hidden="true" />}
      </div>
      <p className="mv-sidebar-search-hint">Type 2+ letters — we match name &amp; patient ID</p>

      {open && results.length > 0 && (
        <ul className="mv-sidebar-search-dropdown" role="listbox">
          {results.map((p) => (
            <li key={p.patient_id}>
              <button type="button" className="mv-sidebar-search-item" onClick={() => openPatient(p)}>
                <span className="mv-sidebar-search-item-id">{p.external_id}</span>
                <span className="mv-sidebar-search-item-name">{p.full_name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && !loading && query.trim().length >= 2 && results.length === 0 && (
        <div className="mv-sidebar-search-empty">No patients found — try a different spelling</div>
      )}
    </div>
  );
}
