import { ReactNode } from "react";
import { Button } from "@/shared/ui/Button/Button";
import styles from "@/shared/ui/AppShell/AppShell.module.css";

type AppShellProps = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  email?: string | null;
  onLogout?: () => Promise<void> | void;
  children: ReactNode;
};

export function AppShell({
  children,
  email,
  eyebrow = "Family Finance",
  onLogout,
  subtitle,
  title,
}: AppShellProps) {
  return (
    <div className={styles.shell}>
      <div className={styles.container}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>{eyebrow}</p>
            <h1 className={styles.title}>{title}</h1>
            {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
          </div>
          <div className={styles.meta}>
            {email ? <span className={styles.email}>{email}</span> : null}
            {onLogout ? (
              <Button variant="secondary" onClick={onLogout}>
                Log out
              </Button>
            ) : null}
          </div>
        </header>
        <main className={styles.content}>{children}</main>
      </div>
    </div>
  );
}
