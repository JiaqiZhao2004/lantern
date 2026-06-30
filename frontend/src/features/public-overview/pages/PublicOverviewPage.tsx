import { Link } from "react-router-dom";
import { accessContact, isRestrictedAuthMode } from "@/features/auth/config/access";
import styles from "@/features/public-overview/pages/PublicOverviewPage.module.css";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { Card } from "@/shared/ui/Card/Card";

const REPO_BASE_URL = "https://github.com/JiaqiZhao2004/lantern";

function repoDoc(path: string) {
  return `${REPO_BASE_URL}/blob/main/${path}`;
}

type WalkthroughStep = {
  number: string;
  eyebrow: string;
  title: string;
  description: string;
  imageSrc: string;
  imageAlt: string;
  slotTitle: string;
  slotNote: string;
  annotations?: Array<{
    label: string;
    text: string;
  }>;
};

type ReceiptCard = {
  eyebrow: string;
  title: string;
  description: string;
  links: Array<{
    label: string;
    href: string;
  }>;
};

function PrimaryAction() {
  const { isLoading, user } = useAuthSession();

  if (isLoading) {
    return (
      <span className={styles.loadingAction} aria-live="polite">
        Checking access
      </span>
    );
  }

  if (user) {
    return (
      <Link className={styles.primaryAction} to="/dashboard">
        Open app
      </Link>
    );
  }

  return (
    <Link className={styles.primaryAction} to="/login">
      {isRestrictedAuthMode ? "Request access or sign in" : "Sign in to explore"}
    </Link>
  );
}

function ClosingAction() {
  const { isLoading, user } = useAuthSession();

  if (isLoading) {
    return (
      <span className={styles.loadingAction} aria-live="polite">
        Session resolving
      </span>
    );
  }

  if (user) {
    return (
      <Link className={styles.primaryAction} to="/dashboard">
        Return to the app
      </Link>
    );
  }

  return (
    <Link className={styles.primaryAction} to="/login">
      {isRestrictedAuthMode ? "Request access or sign in" : "Sign in to verify the flow"}
    </Link>
  );
}

function GitHubMark() {
  return (
    <svg
      aria-hidden="true"
      className={styles.actionIcon}
      viewBox="0 0 24 24"
      focusable="false"
    >
      <path
        fill="currentColor"
        d="M12 1.5A10.5 10.5 0 0 0 8.68 22c.53.1.72-.23.72-.51l-.01-1.98c-2.94.64-3.56-1.24-3.56-1.24-.48-1.2-1.17-1.51-1.17-1.51-.96-.66.07-.65.07-.65 1.06.08 1.61 1.08 1.61 1.08.95 1.61 2.48 1.14 3.09.87.09-.67.37-1.14.67-1.4-2.35-.26-4.83-1.16-4.83-5.18 0-1.15.41-2.09 1.08-2.83-.11-.27-.47-1.35.1-2.81 0 0 .88-.28 2.89 1.08a10.08 10.08 0 0 1 5.26 0c2.01-1.36 2.89-1.08 2.89-1.08.57 1.46.21 2.54.1 2.81.68.74 1.08 1.68 1.08 2.83 0 4.03-2.48 4.91-4.84 5.17.38.32.72.94.72 1.89l-.01 2.8c0 .28.19.61.73.5A10.5 10.5 0 0 0 12 1.5Z"
      />
    </svg>
  );
}

const quickPath = [
  "Sign in with Google or email",
  "Create a household",
  "Link a Plaid Sandbox institution",
  "Inspect shared transaction history",
  "Open a reusable named query",
  "View results in dashboard",
];

const capabilityChips = [
  "Real sign-in",
  "Households",
  "Transactions",
  "Named queries",
  "Plaid Sandbox",
];

const walkthroughSteps: WalkthroughStep[] = [
  {
    number: "01",
    eyebrow: "Entry",
    title: "Sign in with Google or email",
    description:
      "Authentication is live in the public environment, so the first step uses the same account flow as the rest of the app.",
    imageSrc: "/step-1.jpg",
    imageAlt: "Lantern sign-in page with Google and email authentication options.",
    slotTitle: "Sign-in screen",
    slotNote: "Google and email auth",
  },
  {
    number: "02",
    eyebrow: "Setup",
    title: "Create a household",
    description:
      "Household setup is the first product boundary, because the app is organized around who can see and analyze shared financial data.",
    imageSrc: "/step-2.jpg",
    imageAlt: "Lantern household setup page for naming a household and choosing a default currency.",
    slotTitle: "Household setup screen",
    slotNote: "Real household workflow",
  },
  {
    number: "03",
    eyebrow: "Connections",
    title: "Link a Plaid Sandbox institution",
    description:
      "Public financial institution linking uses Plaid Sandbox, which keeps the public environment safe while preserving the real app flow.",
    imageSrc: "/step-3.jpg",
    imageAlt: "Lantern account connection page showing Plaid Sandbox institutions available to link.",
    slotTitle: "Plaid Link flow",
    slotNote: "Sandbox institution linking",
  },
  {
    number: "04",
    eyebrow: "Ledger",
    title: "Inspect transaction history",
    description:
      "Once data is linked, the ledger becomes the calm observability surface: search, filter, and inspect household transaction history without leaving the app.",
    imageSrc: "/step-4.jpg",
    imageAlt: "Lantern transactions page with ledger filters and synced household transactions.",
    slotTitle: "Transactions screen",
    slotNote: "Search, filters, and sorting",
  },
  {
    number: "05",
    eyebrow: "Queries",
    title: "Open a reusable named query",
    description:
      "Named queries are authored and previewed against live household data, so you can refine the draft before deciding what should become a saved reusable view.",
    imageSrc: "/step-5.jpg",
    imageAlt: "Lantern named query editor showing AI-assisted query drafting and a live preview panel.",
    slotTitle: "Named query editor",
    slotNote: "Draft, preview, and validate",
    annotations: [
      {
        label: "Why it is credible",
        text: "The queries are SQL-backed, previewable, and validated before execution, with AI-assisted drafting kept as a secondary aid.",
      },
    ],
  },
  {
    number: "06",
    eyebrow: "Payoff",
    title: "View results in dashboard",
    description:
      "The payoff is reusable analysis over household data rather than one-off browsing. Saved query results stay available in the dashboard as views you can reopen as charts or tables.",
    imageSrc: "/step-6.jpg",
    imageAlt: "Lantern dashboard showing a saved named query result rendered as a table.",
    slotTitle: "Named query result",
    slotNote: "Reusable dashboard view",
    annotations: [
      {
        label: "Why it matters",
        text: "Saved queries turn linked household transactions into reusable views you can reopen as charts or tables.",
      },
    ],
  },
];

const receiptCards: ReceiptCard[] = [
  {
    eyebrow: "Boundaries",
    title: "Inspect household scope",
    description:
      "The core product boundary is who belongs to a household and how shared financial visibility is constrained.",
    links: [
      {
        label: "Inspect membership scope",
        href: repoDoc("docs/adr/0002-one-household-per-user.md"),
      },
      {
        label: "Inspect transaction ownership",
        href: repoDoc(
          "docs/adr/0006-transaction-ownership-and-household-reassignment.md"
        ),
      },
    ],
  },
  {
    eyebrow: "Queries",
    title: "Inspect named query design",
    description:
      "The differentiator is reusable analysis over linked household data, with explicit constraints on how queries are authored and executed.",
    links: [
      {
        label: "Inspect named query design",
        href: repoDoc("docs/adr/0008-named-query-feature-design.md"),
      },
      {
        label: "Inspect SQL restrictions",
        href: repoDoc("docs/adr/0007-named-query-sql-restricted-to-flat-select.md"),
      },
      {
        label: "Inspect AI-assisted drafting",
        href: repoDoc(
          "docs/adr/0012-app-provided-llm-for-named-query-sql-candidates.md"
        ),
      },
    ],
  },
  {
    eyebrow: "Runtime",
    title: "Inspect deployable backend work",
    description:
      "This is not just a local prototype. The repo includes the operational path for a deployed backend runtime and durability work.",
    links: [
      {
        label: "Inspect runtime and durability",
        href: repoDoc(
          "docs/adr/0015-self-hosted-backend-runtime-and-durability.md"
        ),
      },
      {
        label: "Inspect deployment stack",
        href: repoDoc("ops/deployment/backend/app-stack/README.md"),
      },
    ],
  },
  {
    eyebrow: "Observability",
    title: "Inspect observability",
    description:
      "The ops surface includes monitoring and supporting material rather than stopping at a single deploy script.",
    links: [
      {
        label: "Inspect observability",
        href: repoDoc("ops/observability/backend/README.md"),
      },
      {
        label: "Inspect app-native metrics",
        href: repoDoc("docs/adr/0019-app-native-observability-metrics.md"),
      },
    ],
  },
  {
    eyebrow: "Disclosure",
    title: "Inspect the public architecture boundary",
    description:
      "The public environment is intentionally scoped, and the repo documents what is shown publicly versus what remains private.",
    links: [
      {
        label: "Inspect disclosure boundary",
        href: repoDoc("docs/adr/0020-public-architecture-disclosure-boundary.md"),
      },
      {
        label: "Inspect the repository",
        href: REPO_BASE_URL,
      },
    ],
  },
];

export default function PublicOverviewPage() {
  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.eyebrow}>Lantern</p>
          <h1 className={styles.title}>See household finances clearly</h1>
          <p className={styles.summary}>
            Track household finances with linked accounts, shared transaction
            history, and reusable queries.
          </p>
          <p className={styles.environmentNote}>
            {isRestrictedAuthMode
              ? `This Lantern deployment is invite-only. Approved emails can sign in; everyone else should contact ${accessContact}.`
              : "Lantern supports real sign-in, household setup, and app workflows; the public environment uses Plaid Sandbox for financial institution linking."}
          </p>

          <div className={styles.actionRow}>
            <PrimaryAction />
            <a className={styles.secondaryAction} href="#walkthrough">
              See walkthrough
            </a>
            <a
              className={styles.codeAction}
              href={REPO_BASE_URL}
              target="_blank"
              rel="noreferrer"
            >
              <GitHubMark />
              Lookup code
            </a>
          </div>

          <p className={styles.pathNote}>
            {isRestrictedAuthMode
              ? "Built solo as a full-stack systems project. Start with the walkthrough, then request access if you need the private production flow."
              : "Built solo as a full-stack systems project. Start with the walkthrough, then sign in if you want to exercise the full flow yourself."}
          </p>

          <div className={styles.featureList} aria-label="Lantern capabilities">
            {capabilityChips.map((chip) => (
              <span key={chip}>{chip}</span>
            ))}
          </div>
        </div>

        <Card padding="lg" className={styles.heroPanel}>
          <p className={styles.panelEyebrow}>Recommended path</p>
          <h2 className={styles.panelTitle}>What you can test now</h2>
          <p className={styles.panelSummary}>
            Sign in, create a household, link Plaid Sandbox institutions,
            inspect transactions, and open named queries. Authentication and
            household workflows are live; public bank linking uses sandbox
            institutions.
          </p>

          <ol className={styles.pathList}>
            {quickPath.map((item, index) => (
              <li key={item}>
                <span className={styles.pathIndex}>
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ol>
        </Card>
      </section>

      <section className={styles.walkthrough} id="walkthrough">
        <div className={styles.sectionHeader}>
          <p className={styles.sectionEyebrow}>Public walkthrough</p>
          <h2>Follow the app from entry to payoff</h2>
          <p>
            This sequence mirrors the real app flow using the actual public-app
            screens.
          </p>
        </div>

        <div className={styles.stepList}>
          {walkthroughSteps.map((step) => (
            <Card key={step.number} padding="lg" className={styles.stepCard}>
              <div className={styles.stepCopy}>
                <div className={styles.stepHeading}>
                  <span className={styles.stepNumber}>{step.number}</span>
                  <div>
                    <p className={styles.stepEyebrow}>{step.eyebrow}</p>
                    <h3>{step.title}</h3>
                  </div>
                </div>

                <p className={styles.stepDescription}>{step.description}</p>

                {step.annotations ? (
                  <div className={styles.annotationList}>
                    {step.annotations.map((annotation) => (
                      <div key={annotation.label} className={styles.annotation}>
                        <strong>{annotation.label}</strong>
                        <p>{annotation.text}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className={styles.visualSlot}>
                <img
                  className={styles.stepImage}
                  src={step.imageSrc}
                  alt={step.imageAlt}
                  loading="lazy"
                />
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className={styles.receipts}>
        <div className={styles.sectionHeader}>
          <p className={styles.sectionEyebrow}>Engineering receipts</p>
          <h2>Inspect the implementation directly</h2>
          <p>
            These are entry points into the actual product, API, and ops
            material. The goal here is verification, not marketing copy.
          </p>
        </div>

        <div className={styles.receiptGrid}>
          {receiptCards.map((card) => (
            <Card key={card.title} padding="lg" className={styles.receiptCard}>
              <p className={styles.receiptEyebrow}>{card.eyebrow}</p>
              <h3>{card.title}</h3>
              <p className={styles.receiptDescription}>{card.description}</p>
              <div className={styles.receiptLinks}>
                {card.links.map((link) => (
                  <a
                    key={link.label}
                    className={styles.receiptLink}
                    href={link.href}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className={styles.closing}>
        <Card padding="lg" className={styles.closingCard}>
          <p className={styles.sectionEyebrow}>Try it yourself</p>
          <h2>Use the public app when you are ready to verify the flow.</h2>
          <p>
            {isRestrictedAuthMode
              ? `This deployment is limited to approved users. If you need access, contact ${accessContact}.`
              : "Real sign-in, household setup, and app workflows are available in the public environment. Financial institution linking stays on Plaid Sandbox."}
          </p>
          <div className={styles.closingActions}>
            <ClosingAction />
          </div>
        </Card>
      </section>
    </main>
  );
}
