"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2, LogIn, UserPlus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "setup" | "checking">("checking");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      api.getMe()
        .then(() => router.replace("/"))
        .catch(() => {
          localStorage.removeItem("token");
          checkSetup();
        });
    } else {
      checkSetup();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function checkSetup() {
    try {
      await api.getMe();
      setMode("login");
    } catch (err) {
      const msg = (err as Error).message || "";
      if (msg.includes("404") || msg.includes("setup")) {
        setMode("setup");
      } else {
        setMode("login");
      }
    }
  }

  const handleLogin = async () => {
    if (!email || !password) { toast.error("Email and password required"); return; }
    setSubmitting(true);
    try {
      const res = await api.login(email, password);
      localStorage.setItem("token", res.access_token);
      toast.success("Welcome back!");
      router.replace("/");
    } catch {
      toast.error("Invalid credentials");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSetup = async () => {
    if (!email || !password) { toast.error("Email and password required"); return; }
    if (password !== confirmPassword) { toast.error("Passwords do not match"); return; }
    if (password.length < 6) { toast.error("Password must be at least 6 characters"); return; }
    setSubmitting(true);
    try {
      const res = await api.setup(email, password);
      localStorage.setItem("token", res.access_token);
      toast.success("Account created! Welcome to AgenticForce.");
      router.replace("/");
    } catch {
      toast.error("Setup failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (mode === "checking") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm mx-auto">
        <div className="flex flex-col items-center mb-8">
          <div className="h-14 w-14 rounded-2xl bg-primary flex items-center justify-center mb-4">
            <Sparkles className="h-7 w-7 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">AgenticForce</h1>
          <p className="text-sm text-muted-foreground mt-1">AI Creative Agency Platform</p>
        </div>

        <Card className="bg-card border-border">
          <CardHeader className="text-center">
            <CardTitle>{mode === "setup" ? "Create Account" : "Sign In"}</CardTitle>
            <CardDescription>
              {mode === "setup"
                ? "Set up your admin account to get started"
                : "Enter your credentials to continue"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => { e.preventDefault(); mode === "setup" ? handleSetup() : handleLogin(); }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  autoComplete="email"
                  autoFocus
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete={mode === "setup" ? "new-password" : "current-password"}
                />
              </div>
              {mode === "setup" && (
                <div className="space-y-1.5">
                  <Label htmlFor="confirm">Confirm Password</Label>
                  <Input
                    id="confirm"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                  />
                </div>
              )}
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : mode === "setup" ? (
                  <UserPlus className="h-4 w-4 mr-2" />
                ) : (
                  <LogIn className="h-4 w-4 mr-2" />
                )}
                {mode === "setup" ? "Create Account" : "Sign In"}
              </Button>
            </form>
            {mode === "login" && (
              <button
                type="button"
                className="w-full text-center text-xs text-muted-foreground mt-4 hover:text-foreground transition-colors"
                onClick={() => setMode("setup")}
              >
                First time? Set up an account
              </button>
            )}
            {mode === "setup" && (
              <button
                type="button"
                className="w-full text-center text-xs text-muted-foreground mt-4 hover:text-foreground transition-colors"
                onClick={() => setMode("login")}
              >
                Already have an account? Sign in
              </button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
