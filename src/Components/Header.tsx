import { logoutFirebase } from "../features/auth/api/firebase/client";

interface HeaderProps {
  userName?: string | null;
  userEmail?: string | null;
}

function Header({ userName, userEmail }: HeaderProps) {
  const handleLogout = async () => {
    try {
      await logoutFirebase();
    } catch (err) {
      console.error("Logout failed", err);
    }
  };
  return (
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <h2>Dashboard</h2>
      {(userName || userEmail) && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", fontSize: "0.9rem" }}>
          {userName && <span style={{ fontWeight: 600 }}>{userName}</span>}
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
