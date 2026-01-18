import { useContext, useEffect } from "react";
import { AuthContext } from "../AuthContext";
import { useNavigate } from "react-router-dom";
import { userHasSms2FA } from "../auth.api";

export default function MFAVerifyPage() {
  const ctx = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    console.log(ctx);
    if (!ctx) return;

    if (!ctx.state.user) {
      navigate("/login", { replace: true });
      return;
    }

    if (!ctx.state.user.emailVerified) {
      navigate("/verify-email", { replace: true });
      return;
    }

    userHasSms2FA().then((hasSms2FA) => {
      if (!hasSms2FA) {
        navigate("/mfa/setup", { replace: true });
      }
    });
  }, [ctx, navigate]);

  return <div>v</div>;
}
