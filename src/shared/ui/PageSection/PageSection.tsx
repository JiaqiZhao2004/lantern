import { ReactNode } from "react";
import styles from "@/shared/ui/PageSection/PageSection.module.css";

type PageSectionProps = {
  title: string;
  description?: string;
  children: ReactNode;
};

export function PageSection({
  children,
  description,
  title,
}: PageSectionProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>{title}</h2>
          {description ? <p className={styles.description}>{description}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
