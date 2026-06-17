import { ReactNode } from "react";
import { Card } from "@/shared/ui/Card/Card";
import styles from "@/shared/ui/FullPageState/FullPageState.module.css";

type FullPageStateProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
};

export function FullPageState({
  actions,
  description,
  title,
}: FullPageStateProps) {
  return (
    <div className={styles.state}>
      <Card className={styles.card}>
        <h1 className={styles.title}>{title}</h1>
        {description ? <p className={styles.description}>{description}</p> : null}
        {actions ? <div className={styles.actions}>{actions}</div> : null}
      </Card>
    </div>
  );
}
