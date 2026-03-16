"use client";

import * as Select from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "../../lib/cn";

const EMPTY_VALUE_SENTINEL = "__empty__";

export function SelectField({
  className,
  label,
  onValueChange,
  options = [],
  placeholder = "Select",
  value,
}) {
  const normalizedValue = value === "" ? EMPTY_VALUE_SENTINEL : value;

  return (
    <label className={cn("field-shell", className)}>
      {label ? <span className="field-shell__label">{label}</span> : null}
      <Select.Root
        onValueChange={(nextValue) =>
          onValueChange(nextValue === EMPTY_VALUE_SENTINEL ? "" : nextValue)
        }
        value={normalizedValue}
      >
        <Select.Trigger aria-label={label || placeholder} className="ui-select">
          <Select.Value placeholder={placeholder} />
          <Select.Icon className="ui-select__icon">
            <ChevronDown size={16} strokeWidth={2} />
          </Select.Icon>
        </Select.Trigger>
        <Select.Portal>
          <Select.Content
            className="ui-select__content"
            position="popper"
            side="bottom"
            sideOffset={8}
          >
            <Select.Viewport className="ui-select__viewport">
              {options.map((option) => (
                <Select.Item
                  className="ui-select__item"
                  key={option.value}
                  value={option.value === "" ? EMPTY_VALUE_SENTINEL : String(option.value)}
                >
                  <Select.ItemText>{option.label}</Select.ItemText>
                  <Select.ItemIndicator className="ui-select__item-indicator">
                    <Check size={14} strokeWidth={2.25} />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </label>
  );
}
