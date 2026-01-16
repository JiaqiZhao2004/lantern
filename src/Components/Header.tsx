import LogoutButton from "../features/auth/LogoutButton";

function Header() {
  return (
    <header style={{ display: "flex", justifyContent: "space-between" }}>
      <h2>My App</h2>
      <LogoutButton />
    </header>
  );
}

export default Header;
