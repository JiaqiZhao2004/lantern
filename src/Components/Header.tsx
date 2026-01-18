import { logoutFirebase } from "../features/auth/auth.api";

function Header() {
  
  const handleLogout = async () => {
    try {
      await logoutFirebase();
    } catch (err) {
      console.error("Logout failed", err);
    }
  };
  return (
    <header style={{ display: "flex", justifyContent: "space-between" }}>
      <h2>My App</h2>
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
