import { useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";

function AuthShell({ mode }: { mode: "login" | "signup" }) {
  const { token, login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [googleConfigured, setGoogleConfigured] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.googleStatus().then(({ configured }) => setGoogleConfigured(configured)).catch(() => undefined);
  }, []);

  if (token) return <Navigate to="/" replace />;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await signup(email, password, displayName);
      const from = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function googleSignIn() {
    try {
      const { url } = await api.googleStart();
      window.location.assign(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
    }
  }

  const signupMode = mode === "signup";
  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <div className="kicker">USA-NA-AIO practice</div>
        <h1>{signupMode ? "Create your account" : "Welcome back"}</h1>
        <p className="muted">{signupMode ? "Save your progress across study sessions." : "Sign in to continue your course."}</p>
        {signupMode && (
          <div className="field">
            <label htmlFor="display-name">Display name</label>
            <input id="display-name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
          </div>
        )}
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" minLength={signupMode ? 8 : undefined} autoComplete={signupMode ? "new-password" : "current-password"} value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="error">{error}</p>}
        <button className="btn auth-submit" disabled={busy}>{busy ? "Please wait…" : signupMode ? "Sign up" : "Log in"}</button>
        <div className="auth-divider"><span>or</span></div>
        <button className="btn ghost auth-submit" type="button" disabled={!googleConfigured} onClick={googleSignIn}>Continue with Google</button>
        {!googleConfigured && <p className="auth-note">Add Google OAuth keys in backend .env later</p>}
        <p className="auth-switch">
          {signupMode ? "Already have an account? " : "New here? "}
          <Link to={signupMode ? "/login" : "/signup"}>{signupMode ? "Log in" : "Sign up"}</Link>
        </p>
      </form>
    </div>
  );
}

export const LoginPage = () => <AuthShell mode="login" />;
export const SignupPage = () => <AuthShell mode="signup" />;

export function AuthCallbackPage() {
  const [params] = useSearchParams();
  const { acceptToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const token = params.get("token");

  useEffect(() => {
    if (!token) {
      setError("Missing authentication token.");
      return;
    }
    acceptToken(token)
      .then(() => navigate("/", { replace: true }))
      .catch((err: Error) => setError(err.message));
    // Run once for the callback token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (error) return <div className="auth-page"><div className="card auth-card"><p className="error">{error}</p><Link to="/login">Return to login</Link></div></div>;
  return <div className="auth-page"><p className="muted">Finishing sign in…</p></div>;
}
