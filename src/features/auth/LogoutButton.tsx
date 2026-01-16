import React from "react";
import { useNavigate } from "react-router-dom";
import { signOut } from "firebase/auth";
import { auth } from "./firebase";

const LogoutButton: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate("/login", { replace: true });
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  return (
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
  );
};

export default LogoutButton;
