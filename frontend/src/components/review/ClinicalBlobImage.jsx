import { useEffect, useRef, useState } from "react";
import { HttpClient } from "../../services/httpClient";

/** Loads an authenticated clinical image blob from the API. */
export function ClinicalBlobImage({
  url,
  alt,
  className,
  style,
  emptyMessage = "Image not available.",
  onLoaded,
  onImageLayout,
  onError,
}) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState("");
  const onLoadedRef = useRef(onLoaded);
  const onErrorRef = useRef(onError);
  onLoadedRef.current = onLoaded;
  onErrorRef.current = onError;

  useEffect(() => {
    if (!url) {
      setSrc(null);
      setError("");
      return undefined;
    }

    let objectUrl = null;
    setError("");
    HttpClient.requestBlob(url)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
        onLoadedRef.current?.();
      })
      .catch((err) => {
        const message = err.message || "Could not load image.";
        setError(message);
        setSrc(null);
        onErrorRef.current?.(message);
      });

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  if (!url) {
    return emptyMessage ? <p className="cv-imaging-empty">{emptyMessage}</p> : null;
  }
  if (error) {
    return <p className="cv-imaging-empty">{error}</p>;
  }
  if (!src) {
    return <div className="cv-imaging-skeleton" aria-hidden="true" />;
  }
  return (
    <img
      className={className}
      style={style}
      src={src}
      alt={alt}
      onLoad={(event) => {
        onLoadedRef.current?.();
        onImageLayout?.(event.currentTarget);
      }}
    />
  );
}
