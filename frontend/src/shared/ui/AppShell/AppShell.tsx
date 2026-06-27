import { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { Button } from "@/shared/ui/Button/Button";
import styles from "@/shared/ui/AppShell/AppShell.module.css";

type NavClickEvent = React.MouseEvent<HTMLAnchorElement, MouseEvent>;

type AppShellProps = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  email?: string | null;
  onLogout?: () => Promise<void> | void;
  onNavLinkClick?: (event: NavClickEvent) => void;
  children: ReactNode;
};

export function AppShell({
  children,
  email,
  eyebrow = "Lantern",
  onNavLinkClick,
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
            <nav className={styles.nav}>
              <NavLink
                to="/dashboard"
                onClick={onNavLinkClick}
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
                }
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/transactions"
                onClick={onNavLinkClick}
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
                }
              >
                Transactions
              </NavLink>
              <NavLink
                to="/settings"
                onClick={onNavLinkClick}
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
                }
              >
                Settings
              </NavLink>
            </nav>
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
