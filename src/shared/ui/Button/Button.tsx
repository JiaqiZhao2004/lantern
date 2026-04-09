import classNames from "classnames";
import { ButtonHTMLAttributes } from "react";
import styles from "@/shared/ui/Button/Button.module.css";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  fullWidth?: boolean;
};

export function Button({
  className,
  variant = "primary",
  fullWidth = false,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      type={type}
      className={classNames(
        styles.button,
        styles[variant],
        fullWidth && styles.fullWidth,
        className
      )}
    />
  );
}
