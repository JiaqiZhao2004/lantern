import { InputHTMLAttributes } from "react";
import styles from "@/shared/ui/TextField/TextField.module.css";

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> & {
  label: string;
  error?: string | null;
  hint?: string;
  onChange?: (value: string) => void;
};

export function TextField({
  error,
  hint,
  id,
  label,
  onChange,
  ...props
}: TextFieldProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <input
        {...props}
        id={inputId}
        className={styles.input}
        onChange={(event) => onChange?.(event.target.value)}
      />
      {error ? (
        <span className={styles.error}>{error}</span>
      ) : hint ? (
        <span className={styles.hint}>{hint}</span>
      ) : null}
    </div>
  );
}
