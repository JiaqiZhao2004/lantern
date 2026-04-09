import classNames from "classnames";
import { HTMLAttributes } from "react";
import styles from "@/shared/ui/Card/Card.module.css";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  padding?: "md" | "lg";
};

export function Card({
  children,
  className,
  padding = "lg",
  ...props
}: CardProps) {
  return (
    <div
      {...props}
      className={classNames(
        styles.card,
        padding === "md" ? styles["padding-md"] : styles["padding-lg"],
        className
      )}
    >
      {children}
    </div>
  );
}
