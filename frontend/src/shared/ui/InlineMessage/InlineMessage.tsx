import classNames from "classnames";
import { HTMLAttributes } from "react";
import styles from "@/shared/ui/InlineMessage/InlineMessage.module.css";

type InlineMessageProps = HTMLAttributes<HTMLDivElement> & {
  tone?: "info" | "success" | "error";
};

export function InlineMessage({
  children,
  className,
  tone = "info",
  ...props
}: InlineMessageProps) {
  return (
    <div
      {...props}
      className={classNames(styles.message, styles[tone], className)}
    >
      {children}
    </div>
  );
}
