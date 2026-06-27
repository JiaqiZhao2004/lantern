import { useNavigate } from "react-router-dom";
import { accessContact } from "@/features/auth/config/access";
import styles from "@/features/auth/components/RestrictedAccessPanel.module.css";
import { Button } from "@/shared/ui/Button/Button";
import { Card } from "@/shared/ui/Card/Card";

type RestrictedAccessPanelProps = {
  title?: string;
  description?: string;
  detail?: string;
  showSignInHint?: boolean;
  onLogout?: () => void;
};

export function RestrictedAccessPanel({
  title = "This Lantern site is invite-only",
  description = "Only pre-approved email addresses can enter this deployment. If you need access, contact the owner and ask to be added to the production allowlist.",
  detail,
  showSignInHint = false,
  onLogout,
}: RestrictedAccessPanelProps) {
  const navigate = useNavigate();

  return (
    <Card padding="lg" className={styles.panel}>
      <div>
        <p className={styles.eyebrow}>Restricted access</p>
        <h2 className={styles.title}>{title}</h2>
        <p className={styles.description}>{description}</p>
      </div>

      <p className={styles.note}>
        Contact <span className={styles.contact}>{accessContact}</span> for access.
        {detail ? ` ${detail}` : ""}
      </p>

      <div className={styles.chipRow} aria-label="Access requirements">
        <span className={styles.chip}>Approved email required</span>
        <span className={styles.chip}>Production deployment only</span>
        {showSignInHint ? <span className={styles.chip}>Authorized users can sign in below</span> : null}
      </div>

      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => navigate("/")}>
          Back to overview
        </Button>
        {onLogout ? <Button onClick={onLogout}>Sign out</Button> : null}
      </div>
    </Card>
  );
}
