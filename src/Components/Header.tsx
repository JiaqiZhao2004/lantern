import { logoutFirebase } from "../features/auth/api/firebase/client";

interface HeaderProps {
  householdName?: string | null;
  userEmail?: string | null;
}

function Header({ householdName, userEmail }: HeaderProps) {
  const handleLogout = async () => {
    try {
      await logoutFirebase();
    } catch (err) {
      console.error("Logout failed", err);
    }
  };
  return (
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div>
        <h2 style={{ marginBottom: householdName ? "0.2rem" : 0 }}>Dashboard</h2>
        {householdName && (
          <div style={{ color: "#555", fontSize: "0.95rem", fontWeight: 600 }}>
            {householdName}
          </div>
        )}
      </div>
      {userEmail && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", fontSize: "0.9rem" }}>
          {userEmail && <span style={{ color: "#666" }}>{userEmail}</span>}
        </div>
      )}
      <button
        onClick={handleLogout}
        style={{
          padding: "0.4rem 0.7rem",
          borderRadius: "4px",
          border: "1px solid #ccc",
          backgroundColor: "#ffffff",
          cursor: "pointer",
          fontSize: "0.9rem",
        }}
      >
        Log out
      </button>
    </header>
  );
}

export default Header;
