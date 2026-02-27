import { useContext } from "react";
import Button from "plaid-threads/Button";

import Link from "../Link";
import Context from "../../state/Context";

import styles from "./index.module.css";

const LaunchLinkButton = () => {
  const { linkToken } = useContext(Context);

  return (
    <div className={styles.grid}>
      <>
        {linkToken === "" ? (
          <div className={styles.linkButton}>
            <Button large disabled>
              Loading...
            </Button>
          </div>
        ) : (
          <div className={styles.linkButton}>
            <Link />
          </div>
        )}
      </>
    </div>
  );
};

LaunchLinkButton.displayName = "LaunchLinkButton";

export default LaunchLinkButton;
