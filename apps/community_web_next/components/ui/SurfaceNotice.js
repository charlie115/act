"use client";

const VARIANT_CLASS = {
  error: "surface-notice--error",
  info: "surface-notice--info",
  loading: "surface-notice--loading",
};

export default function SurfaceNotice({
  actions = null,
  className = "",
  description,
  title,
  variant = "info",
}) {
  const variantClass = VARIANT_CLASS[variant] || VARIANT_CLASS.info;

  return (
    <div className={`surface-notice ${variantClass} ${className}`.trim()}>
      <div>
        {title ? <strong>{title}</strong> : null}
        {description ? <p>{description}</p> : null}
      </div>
      {actions ? <div className="surface-notice__actions">{actions}</div> : null}
    </div>
  );
}
