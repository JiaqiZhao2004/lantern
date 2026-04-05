import { useCallback, useContext, useEffect, useState } from "react";
import { get_accounts } from "../api/backend/client";
import { ItemWithAccounts } from "../api/backend/dto";
import { DashboardContext } from "../state/DashboardContext";

export default function AccountsPanel() {
  const { linkedDataRefreshKey } = useContext(DashboardContext);
  const [items, setItems] = useState<ItemWithAccounts[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get_accounts();
      setItems(data.items);
    } catch (err) {
      setError("Failed to load accounts.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts, linkedDataRefreshKey]);

  return (
    <div style={{ margin: "1rem 0" }}>
      <h2>Accounts</h2>
      {loading && <p>Loading accounts…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && items.length === 0 && <p>No accounts found.</p>}
      {!loading &&
        !error &&
        items.map((item) => (
          <div key={item.item_id} style={{ marginBottom: "1.5rem" }}>
            <h3 style={{ marginBottom: "0.5rem" }}>
              {item.institution_name ?? item.plaid_item_id}
            </h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Name</th>
                  <th style={thStyle}>Type</th>
                  <th style={thStyle}>Subtype</th>
                  <th style={thStyle}>Mask</th>
                </tr>
              </thead>
              <tbody>
                {(item.accounts ?? []).map((account) => (
                  <tr key={account.id}>
                    <td style={tdStyle}>{account.name}</td>
                    <td style={tdStyle}>{account.account_type ?? "—"}</td>
                    <td style={tdStyle}>{account.account_subtype ?? "—"}</td>
                    <td style={tdStyle}>{account.mask ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "8px 12px",
  borderBottom: "2px solid #ccc",
  fontWeight: 600,
};

const tdStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderBottom: "1px solid #eee",
};
