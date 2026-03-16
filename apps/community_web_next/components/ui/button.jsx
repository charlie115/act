import { cn } from "../../lib/cn";
const VARIANT_CLASSNAME = {
  primary: "ui-button--primary",
  secondary: "ui-button--secondary",
  ghost: "ui-button--ghost",
  subtle: "ui-button--subtle",
};

const SIZE_CLASSNAME = {
  sm: "ui-button--sm",
  md: "ui-button--md",
  lg: "ui-button--lg",
};

export function buttonVariants({ variant = "primary", size = "md" } = {}) {
  return cn("ui-button", VARIANT_CLASSNAME[variant], SIZE_CLASSNAME[size]);
}

export function Button({
  children,
  className,
  size,
  type = "button",
  variant,
  ...props
}) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      type={type}
      {...props}
    >
      {children}
    </button>
  );
}
