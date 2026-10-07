import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useAuth } from "../auth/AuthContext";

const DEMO_EMAIL = import.meta.env.VITE_DEMO_LOGIN_EMAIL ?? "";
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_LOGIN_PASSWORD ?? "";
const SHOW_DEMO = DEMO_EMAIL !== "" && DEMO_PASSWORD !== "";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate(location.state?.from ?? "/", { replace: true });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Login failed. Check your credentials."
      );
    } finally {
      setBusy(false);
    }
  };

  const useDemoCredentials = () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setError(null);
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        p: 2,
      }}
    >
      <Card sx={{ width: "100%", maxWidth: 440 }} variant="outlined">
        <CardContent>
          <Typography variant="h2" component="h1" gutterBottom>
            🌱 Sign in
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Smart Greenhouse Intelligence Platform
          </Typography>
          <form onSubmit={onSubmit}>
            <Stack spacing={2}>
              {error && <Alert severity="error">{error}</Alert>}
              <TextField
                label="Email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                fullWidth
              />
              <TextField
                label="Password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                fullWidth
              />
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={busy}
                fullWidth
              >
                {busy ? "Signing in…" : "Sign in"}
              </Button>

              {SHOW_DEMO && (
                <>
                  <Divider sx={{ my: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Demo access
                    </Typography>
                  </Divider>
                  <Alert
                    severity="info"
                    icon={false}
                    sx={{ alignItems: "flex-start" }}
                  >
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Portfolio demo</strong> — use these credentials to
                      explore the platform:
                    </Typography>
                    <Stack
                      component="dl"
                      spacing={0.5}
                      sx={{
                        m: 0,
                        fontFamily: "monospace",
                        fontSize: "0.85rem",
                      }}
                    >
                      <Box component="div" sx={{ display: "flex", gap: 1 }}>
                        <Typography
                          component="dt"
                          variant="caption"
                          sx={{ minWidth: 72, color: "text.secondary" }}
                        >
                          Email:
                        </Typography>
                        <Typography
                          component="dd"
                          variant="caption"
                          sx={{ m: 0, fontFamily: "monospace" }}
                        >
                          {DEMO_EMAIL}
                        </Typography>
                      </Box>
                      <Box component="div" sx={{ display: "flex", gap: 1 }}>
                        <Typography
                          component="dt"
                          variant="caption"
                          sx={{ minWidth: 72, color: "text.secondary" }}
                        >
                          Password:
                        </Typography>
                        <Typography
                          component="dd"
                          variant="caption"
                          sx={{ m: 0, fontFamily: "monospace" }}
                        >
                          {DEMO_PASSWORD}
                        </Typography>
                      </Box>
                    </Stack>
                    <Button
                      size="small"
                      variant="outlined"
                      sx={{ mt: 1.5 }}
                      onClick={useDemoCredentials}
                      disabled={busy}
                    >
                      Fill demo credentials
                    </Button>
                  </Alert>
                </>
              )}
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}