import { Link } from "react-router-dom";
import styles from "@/features/public-overview/pages/PublicOverviewPage.module.css";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { Card } from "@/shared/ui/Card/Card";

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
    <a className={styles.primaryAction} href="#preview">
      Try preview
    </a>
  );
}

const sampleTransactions = [
  { name: "Payroll Deposit", account: "Household Checking", amount: "+$4,980" },
  { name: "Rent Transfer", account: "Joint Bills", amount: "-$2,100" },
  { name: "Neighborhood Grocer", account: "Household Checking", amount: "-$128" },
  { name: "Utilities", account: "Joint Bills", amount: "-$94" },
];

const workflowSteps = [
  {
    title: "Bring the household into one view",
    description:
      "Lantern is designed to pull linked checking, savings, and credit accounts into a shared operating picture.",
  },
  {
    title: "Explore shared financial visibility",
    description:
      "The demo emphasizes how a household could inspect inflow, outflow, and account activity in one workspace.",
  },
  {
    title: "Prototype reusable analysis views",
    description:
      "Named Queries show the intended analysis layer: repeatable household views backed by validated SQL.",
  },
];

const implementationReceipts = [
  "Household-scoped data model and membership boundaries",
  "Validated read-only Named Queries with LLM-assisted draft generation",
  "Plaid-backed item linking and household account listing endpoints",
  "FastAPI + PostgreSQL backend with typed React frontend",
  "Public preview isolated from the private production workspace",
];

const savedViews = [
  "Monthly free cash",
  "Fixed vs flexible outflow",
  "Spending changes by category",
];

export default function PublicOverviewPage() {
  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>Lantern</p>
          <h1 className={styles.title}>A prototype for a shared finance workspace</h1>
          <p className={styles.summary}>
            Lantern is a product-minded prototype for shared household finance:
            linked accounts, household visibility, and Named Queries for
            analysis. This public preview is a staged sandbox experience backed
            by sample data and Plaid Sandbox institutions.
          </p>
          <div className={styles.heroActions}>
            <div className={styles.actionRow}>
              <PrimaryAction />
              <a
                className={styles.secondaryAction}
                href="https://github.com/JiaqiZhao2004/lantern-public"
                target="_blank"
                rel="noreferrer"
              >
                See how it&apos;s built
              </a>
            </div>
            <p className={styles.heroNote}>
              The public surface is intentionally sandboxed and selectively
              implemented. The goal is to show product direction and the
              strongest engineering foundations without overstating feature
              completeness.
            </p>
            <div className={styles.featureList} aria-label="Lantern capabilities">
              <span>Shared household visibility</span>
              <span>Cash-flow planning</span>
              <span>Named Queries</span>
            </div>
          </div>
        </div>

        <div className={styles.workspaceStage} id="preview">
          <div className={styles.stageGlow} aria-hidden="true" />
          <div className={styles.workspaceChrome}>
            <span className={styles.chromeDot} />
            <span className={styles.chromeDot} />
            <span className={styles.chromeDot} />
            <p className={styles.workspaceUrl}>lantern / guest preview</p>
          </div>

          <div className={styles.workspaceFrame}>
            <div className={styles.workspaceHeader}>
              <div>
                <p className={styles.mockLabel}>Demo workspace</p>
                <h2 className={styles.mockTitle}>Illustrative household planning view</h2>
              </div>
              <div className={styles.headerMeta}>
                <span className={styles.statusBadge}>Plaid Sandbox linked</span>
                <span className={styles.inlineMeta}>Sample household data</span>
              </div>
            </div>

            <div className={styles.mockMetrics}>
              <Card padding="md" className={styles.metricCard}>
                <p className={styles.metricLabel}>Accounts linked</p>
                <strong className={styles.metricValue}>4</strong>
              </Card>
              <Card padding="md" className={styles.metricCard}>
                <p className={styles.metricLabel}>Monthly free cash</p>
                <strong className={styles.metricValue}>$2,184</strong>
              </Card>
              <Card padding="md" className={styles.metricCard}>
                <p className={styles.metricLabel}>Saved Named Queries</p>
                <strong className={styles.metricValue}>6</strong>
              </Card>
            </div>

            <div className={styles.workspaceGrid}>
              <Card padding="lg" className={styles.insightCard}>
                <div className={styles.cardHeader}>
                  <div>
                    <p className={styles.sectionLabel}>Featured view</p>
                    <h3>Prototype monthly cash summary</h3>
                  </div>
                  <span className={styles.inlineBadge}>Named Query</span>
                </div>
                <div className={styles.insightValueRow}>
                  <strong className={styles.insightValue}>$2,184</strong>
                  <span className={styles.insightDelta}>+12% vs last month</span>
                </div>
                <p className={styles.insightSummary}>
                  This staged example shows the kind of household-level summary
                  Lantern is designed to support through reusable queries.
                </p>
                <div className={styles.chartBars} aria-hidden="true">
                  <span style={{ height: "46%" }} />
                  <span style={{ height: "58%" }} />
                  <span style={{ height: "66%" }} />
                  <span style={{ height: "80%" }} />
                  <span style={{ height: "74%" }} />
                  <span style={{ height: "88%" }} />
                </div>
                <div className={styles.queryBox}>
                  <div className={styles.queryHeader}>
                    <span className={styles.queryBadge}>Named Query</span>
                    <span className={styles.queryState}>Validated read-only SQL</span>
                  </div>
                  <code className={styles.querySnippet}>
                    SELECT month, income - fixed_spend - flexible_spend AS
                    free_cash FROM household_cash_flow
                  </code>
                </div>
              </Card>

              <div className={styles.sideColumn}>
                <Card padding="md" className={styles.mockCard}>
                  <div className={styles.cardHeader}>
                    <div>
                      <p className={styles.sectionLabel}>Saved views</p>
                      <h3>Planning workspace</h3>
                    </div>
                    <span className={styles.inlineBadge}>6 active</span>
                  </div>
                  <ul className={styles.savedViewList}>
                    {savedViews.map((view) => (
                      <li key={view}>
                        <span>{view}</span>
                        <span className={styles.savedViewMeta}>Ready</span>
                      </li>
                    ))}
                  </ul>
                </Card>

                <Card padding="md" className={styles.mockCard}>
                  <div className={styles.cardHeader}>
                    <div>
                      <p className={styles.sectionLabel}>Recent activity</p>
                      <h3>Synced transactions</h3>
                    </div>
                    <span className={styles.inlineBadge}>Latest import</span>
                  </div>
                  <ul className={styles.transactionList}>
                    {sampleTransactions.map((transaction) => (
                      <li key={`${transaction.name}-${transaction.account}`}>
                        <div>
                          <strong>{transaction.name}</strong>
                          <p>{transaction.account}</p>
                        </div>
                        <span>{transaction.amount}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.band}>
        <div className={styles.bandHeader}>
          <p className={styles.bandEyebrow}>Workflow</p>
          <h2>What the prototype is aiming at</h2>
          <p>
            The product direction is still planning and visibility, but this
            page should reflect the current state honestly: a strong interface
            concept backed by a partial implementation.
          </p>
        </div>
        <div className={styles.workflowGrid}>
          {workflowSteps.map((step, index) => (
            <Card key={step.title} className={styles.workflowCard}>
              <span className={styles.stepNumber}>
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className={styles.band}>
        <div className={styles.bandHeader}>
          <p className={styles.bandEyebrow}>Implementation</p>
          <h2>Implemented foundation, not full product depth</h2>
          <p>
            The public preview is intentionally sandboxed, and the backend is
            still incomplete. What exists today is the foundation: scoped data
            access, query validation, Plaid integration paths, and deployment
            isolation.
          </p>
        </div>

        <div className={styles.evidenceGrid}>
          <Card className={styles.evidenceCard}>
            <div className={styles.cardHeader}>
              <div>
                <p className={styles.sectionLabel}>Public preview</p>
                <h3>How the sandbox is constrained</h3>
              </div>
              <span className={styles.inlineBadge}>Safe for review</span>
            </div>
            <ul className={styles.stackList}>
              {implementationReceipts.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>

          <Card className={styles.evidenceCard}>
            <div className={styles.cardHeader}>
              <div>
                <p className={styles.sectionLabel}>What to inspect</p>
                <h3>Where the real implementation lives</h3>
              </div>
              <span className={styles.inlineBadge}>Repo guide</span>
            </div>
            <div className={styles.receiptList}>
              <div className={styles.receiptItem}>
                <strong>Frontend product surface</strong>
                <p>Typed React routes, auth flows, and dashboard-oriented UI composition.</p>
              </div>
              <div className={styles.receiptItem}>
                <strong>Backend boundaries</strong>
                <p>FastAPI modules, household scoping, and API contracts for viewer state.</p>
              </div>
              <div className={styles.receiptItem}>
                <strong>Named Query pipeline</strong>
                <p>LLM-assisted query drafting, validation, and read-only execution guardrails.</p>
              </div>
            </div>
            <a
              className={styles.repoLink}
              href="https://github.com/JiaqiZhao2004/lantern-public"
              target="_blank"
              rel="noreferrer"
            >
              See how it&apos;s built
            </a>
          </Card>
        </div>
      </section>
    </main>
  );
}
