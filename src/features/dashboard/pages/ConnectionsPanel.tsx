import { useCallback, useEffect, useState } from "react";
import { get_items } from "../api/backend/client";
import { PlaidItem } from "../api/backend/dto";

export default function ConnectionsPanel() {
  const [items, setItems] = useState<PlaidItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get_items();
      setItems(data.items);
    } catch (err) {
      setError("Failed to load connections.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  return (
    <div style={{ margin: "1rem 0" }}>
      <h2>Connected Accounts</h2>
      {loading && <p>Loading connections…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={thStyle}>Institution</th>
              <th style={thStyle}>Item ID</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={2} style={{ ...tdStyle, textAlign: "center" }}>
                  No connections found.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id}>
                  <td style={tdStyle}>{item.institution_name ?? "—"}</td>
                  <td style={tdStyle}>{item.plaid_item_id}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
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