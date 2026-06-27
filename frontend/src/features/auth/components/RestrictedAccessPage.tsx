import styles from "@/features/auth/components/RestrictedAccessPage.module.css";
import { RestrictedAccessPanel } from "@/features/auth/components/RestrictedAccessPanel";

type RestrictedAccessPageProps = {
  detail: string;
  onLogout: () => Promise<void>;
};

export function RestrictedAccessPage({
  detail,
  onLogout,
}: RestrictedAccessPageProps) {
  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <RestrictedAccessPanel detail={detail} onLogout={() => void onLogout()} />
      </div>
    </main>
  );
}
