import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import classNames from "classnames";
import styles from "@/features/named-queries/pages/NamedQueryEditorPage.module.css";
import { NamedQueryResultTable } from "@/features/named-queries/components/NamedQueryResultTable";
import {
  useCreateNamedQueryMutation,
  useGenerateNamedQueryMutation,
  useNamedQueriesQuery,
  usePatchNamedQueryMutation,
  usePreviewNamedQueryMutation,
} from "@/features/named-queries/api/queries";
import { KNOWN_CHART_TYPES } from "@/features/named-queries/api/contracts";
import type {
  ChartType,
  NamedQueryGenerationMessage,
} from "@/features/named-queries/api/contracts";
import { AppShell } from "@/shared/ui/AppShell/AppShell";
import { Button } from "@/shared/ui/Button/Button";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useViewerQuery } from "@/features/viewer/api/queries";
import { useHouseholdQuery } from "@/features/household/api/queries";

type NamedQueryDraft = {
  name: string;
  sql: string;
  chartType: ChartType | null;
};

function normalizeChartType(value: string | null | undefined): ChartType | null {
  return KNOWN_CHART_TYPES.includes(value as ChartType) ? (value as ChartType) : null;
}

function formatDraftContext(draft: NamedQueryDraft): string {
  return [
    "Current Named Query",
    `name: ${draft.name || "(untitled)"}`,
    `chart_type: ${draft.chartType ?? "table"}`,
    "sql_query:",
    draft.sql || "(empty)",
  ].join("\n");
}

function formatCandidateMessage(draft: NamedQueryDraft): string {
  return [
    `Applied name: ${draft.name}`,
    `chart_type: ${draft.chartType ?? "table"}`,
    "sql_query:",
    draft.sql,
  ].join("\n");
}

export default function NamedQueryEditorPage() {
  const { id } = useParams<{ id?: string }>();
  const isEditing = Boolean(id);
  const navigate = useNavigate();

  const { logout, user } = useAuthSession();
  const viewerQuery = useViewerQuery({ enabled: true });
  const householdQuery = useHouseholdQuery({ enabled: true });

  const listQuery = useNamedQueriesQuery();
  const existing = id ? listQuery.data?.find((q) => q.id === id) : undefined;

  const [name, setName] = useState("");
  const [sql, setSql] = useState("");
  const [chartType, setChartType] = useState<ChartType | null>(null);
  const [aiInput, setAiInput] = useState("");
  const [aiMessages, setAiMessages] = useState<NamedQueryGenerationMessage[]>([]);
  const [aiMessage, setAiMessage] = useState<string | null>(null);
  const [lastAiAppliedDraft, setLastAiAppliedDraft] = useState<NamedQueryDraft | null>(null);
  const [seededQueryId, setSeededQueryId] = useState<string | null>(null);

  useEffect(() => {
    if (existing) {
      setName(existing.name);
      setSql(existing.sql_query);
      setChartType(normalizeChartType(existing.chart_type));
    }
  }, [existing]);

  useEffect(() => {
    if (!isEditing) {
      setSeededQueryId(null);
      return;
    }

    if (!existing || seededQueryId === existing.id) {
      return;
    }

    setAiMessages([
      {
        role: "assistant",
        content: formatDraftContext({
          name: existing.name,
          sql: existing.sql_query,
          chartType: normalizeChartType(existing.chart_type),
        }),
      },
    ]);
    setAiMessage(null);
    setAiInput("");
    setLastAiAppliedDraft(null);
    setSeededQueryId(existing.id);
  }, [existing, isEditing, seededQueryId]);

  const createMutation = useCreateNamedQueryMutation();
  const patchMutation = usePatchNamedQueryMutation(id ?? "");
  const previewMutation = usePreviewNamedQueryMutation();
  const generateMutation = useGenerateNamedQueryMutation();

  const isSaving = createMutation.isPending || patchMutation.isPending;
  const saveError = createMutation.error ?? patchMutation.error;

  const handlePreview = () => {
    if (sql.trim()) previewMutation.mutate({ sql_query: sql });
  };

  const handleSave = async () => {
    if (!name.trim() || !sql.trim()) return;
    if (isEditing && id) {
      await patchMutation.mutateAsync({ name, sql_query: sql, chart_type: chartType });
    } else {
      await createMutation.mutateAsync({ name, sql_query: sql, chart_type: chartType });
    }
    navigate("/dashboard");
  };

  const handleGenerate = async () => {
    const content = aiInput.trim();
    if (!content) return;

    const nextMessages: NamedQueryGenerationMessage[] = [
      ...aiMessages,
      { role: "member", content },
    ];
    setAiMessages(nextMessages);
    setAiInput("");
    setAiMessage(null);

    const response = await generateMutation.mutateAsync({ messages: nextMessages });
    if (response.type === "clarifying_question") {
      const question = response.question;
      setAiMessages([...nextMessages, { role: "assistant", content: question }]);
      return;
    }

    if (response.type === "explanation") {
      setAiMessages([...nextMessages, { role: "assistant", content: response.message }]);
      return;
    }

    if (response.type === "generation_failure") {
      setAiMessage(response.message);
      return;
    }

    if (response.type === "named_query_candidate") {
      const previousDraft: NamedQueryDraft = {
        name,
        sql,
        chartType,
      };
      const nextDraft: NamedQueryDraft = {
        name: response.name,
        sql: response.candidate.sql_query,
        chartType: normalizeChartType(response.candidate.chart_type),
      };

      setLastAiAppliedDraft(previousDraft);
      setName(response.name);
      setSql(nextDraft.sql);
      setChartType(nextDraft.chartType);
      setAiMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: formatCandidateMessage(nextDraft),
        },
      ]);
      setAiMessage(
        isEditing
          ? "Applied AI changes to the draft. Preview, undo if needed, then save."
          : "Generated a query candidate. Review it, preview it, then save."
      );
    }
  };

  const handleUndoAi = () => {
    if (!lastAiAppliedDraft) return;
    setName(lastAiAppliedDraft.name);
    setSql(lastAiAppliedDraft.sql);
    setChartType(lastAiAppliedDraft.chartType);
    setLastAiAppliedDraft(null);
    setAiMessage("Reverted the last AI-applied change.");
  };

  const title = householdQuery.data?.name ?? viewerQuery.data?.name ?? "Dashboard";

  return (
    <AppShell
      title={isEditing ? "Edit Named Query" : "New Named Query"}
      email={user?.email ?? viewerQuery.data?.email}
      onLogout={logout}
    >
      <div className={styles.layout}>
        <Card padding="lg">
          <div className={styles.form}>
            <div className={styles.aiPanel}>
              <div>
                <h2 className={styles.aiTitle}>AI assist</h2>
                <p className={styles.hint}>
                  {isEditing
                    ? "Ask the assistant to explain or revise this Named Query. AI changes apply to the draft immediately until you save."
                    : "Describe the Named Query you want. The assistant can ask up to three clarifying questions, one at a time, before it fills the form below."}
                </p>
              </div>

              {aiMessages.length > 0 && (
                <div className={styles.aiTranscript}>
                  {aiMessages.map((message, index) => (
                    <div
                      key={`${message.role}-${index}`}
                      className={classNames(
                        styles.aiBubble,
                        message.role === "member" ? styles.memberBubble : styles.assistantBubble
                      )}
                    >
                      {message.content}
                    </div>
                  ))}
                </div>
              )}

              {aiMessage && <InlineMessage>{aiMessage}</InlineMessage>}
              {generateMutation.isError && (
                <InlineMessage tone="error">
                  {generateMutation.error instanceof Error
                    ? generateMutation.error.message
                    : "Generation failed."}
                </InlineMessage>
              )}

              <div className={styles.aiControls}>
                <input
                  value={aiInput}
                  onChange={(e) => setAiInput(e.target.value)}
                  placeholder={
                    isEditing
                      ? "e.g. Explain this query or change it to monthly grocery spending"
                      : aiMessages.some((message) => message.role === "assistant")
                        ? "Answer the clarifying question to continue"
                        : "e.g. Show grocery spending by month"
                  }
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleGenerate();
                    }
                  }}
                />
                <Button
                  variant="secondary"
                  onClick={handleGenerate}
                  disabled={generateMutation.isPending || !aiInput.trim()}
                >
                  {generateMutation.isPending ? "Thinking…" : "Ask AI"}
                </Button>
              </div>

              {lastAiAppliedDraft && (
                <div className={styles.aiActions}>
                  <Button variant="ghost" onClick={handleUndoAi}>
                    Undo last AI change
                  </Button>
                </div>
              )}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="nq-name">
                Name
              </label>
              <input
                id="nq-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Spending by category"
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="nq-sql">
                SQL
              </label>
              <p className={styles.hint}>
                Flat SELECT only — no CTEs or subqueries. Query{" "}
                <code>widget_transactions</code> or <code>widget_accounts</code>. Do not
                filter by <code>household_id</code>.
              </p>
              <textarea
                id="nq-sql"
                className={styles.sqlTextarea}
                value={sql}
                onChange={(e) => setSql(e.target.value)}
                placeholder={
                  "SELECT category, SUM(amount) AS total\nFROM widget_transactions\nGROUP BY category\nORDER BY total ASC"
                }
                spellCheck={false}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Chart type</label>
              <div className={styles.chartTypeGroup}>
                <button
                  type="button"
                  className={classNames(
                    styles.chartTypeOption,
                    chartType === null && styles.selected
                  )}
                  onClick={() => setChartType(null)}
                >
                  Table only
                </button>
                {KNOWN_CHART_TYPES.map((type) => (
                  <button
                    key={type}
                    type="button"
                    className={classNames(
                      styles.chartTypeOption,
                      chartType === type && styles.selected
                    )}
                    onClick={() => setChartType(type)}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)} chart
                  </button>
                ))}
              </div>
            </div>

            {saveError instanceof Error && (
              <InlineMessage tone="error">{saveError.message}</InlineMessage>
            )}

            <div className={styles.formActions}>
              <Button
                onClick={handleSave}
                disabled={isSaving || !name.trim() || !sql.trim()}
              >
                {isSaving ? "Saving…" : "Save"}
              </Button>
              <Button variant="secondary" onClick={handlePreview} disabled={!sql.trim()}>
                Preview
              </Button>
              <Button variant="ghost" onClick={() => navigate("/dashboard")}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>

        <div className={styles.previewPanel}>
          <div className={styles.previewHeader}>
            <h2 className={styles.previewTitle}>Preview</h2>
          </div>

          <Card padding="md">
            {!previewMutation.data && !previewMutation.isPending && !previewMutation.isError && (
              <p className={styles.previewEmpty}>
                Write a query and click Preview to see results.
              </p>
            )}

            {previewMutation.isPending && (
              <p className={styles.previewEmpty}>Running…</p>
            )}

            {previewMutation.isError && (
              <InlineMessage tone="error">
                {previewMutation.error instanceof Error
                  ? previewMutation.error.message
                  : "Preview failed."}
              </InlineMessage>
            )}

            {previewMutation.data && (
              <NamedQueryResultTable
                columns={previewMutation.data.columns}
                rows={previewMutation.data.rows as Record<string, unknown>[]}
                truncated={previewMutation.data.truncated}
              />
            )}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
