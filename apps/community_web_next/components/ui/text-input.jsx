"use client";

import { Search } from "lucide-react";

import { cn } from "../../lib/cn";

export function TextInput({
  className,
  label,
  onChange,
  placeholder,
  value,
}) {
  return (
    <label className={cn("field-shell", className)}>
      {label ? <span className="field-shell__label">{label}</span> : null}
      <span className="ui-input-shell">
        <Search className="ui-input-shell__icon" size={16} strokeWidth={2} />
        <input
          className="ui-input-shell__input"
          onChange={onChange}
          placeholder={placeholder}
          value={value}
        />
      </span>
    </label>
  );
}
