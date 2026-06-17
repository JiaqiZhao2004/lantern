import { ReactNode } from "react";
import { Card } from "@/shared/ui/Card/Card";
import styles from "@/features/auth/components/AuthPageLayout.module.css";

type AuthPageLayoutProps = {
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
};

export function AuthPageLayout({
  children,
  description,
  footer,
  title,
}: AuthPageLayoutProps) {
  return (
    <div className={styles.page}>
      <Card className={styles.card}>
        <div>
          <h1 className={styles.title}>{title}</h1>
          <p className={styles.description}>{description}</p>
        </div>
        <div className={styles.content}>{children}</div>
        {footer ? <div className={styles.footer}>{footer}</div> : null}
      </Card>
    </div>
  );
}
