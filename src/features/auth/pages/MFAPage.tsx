import { useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../AuthContext";
// Components
// API
import { userHasSms2FA } from "../auth.api";

export default function MFAPage() {
  const ctx = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (!ctx) return;

    if (!ctx.state.user) {
      navigate("/login", { replace: true });
      return;
    }

    if (!ctx.state.user.emailVerified) {
      navigate("/verify-email", { replace: true });
      return;
    }

    // userHasSms2FA().then((hasSms2FA) => {
    //   if (hasSms2FA) {
    //     navigate("/verify-2fa", { replace: true });
    //   } else {
    //     navigate("/setup-2fa", { replace: true });
    //   }
    // });
  }, [ctx, navigate]);

  return <div>MFA</div>;
}
