import { type FormEvent, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { AuthLayout } from "../components/auth/AuthLayout";
import { FormField } from "../components/auth/FormField";
import { ApiError } from "../lib/api";
import { authService } from "../services/auth-service";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get("token") ?? "", [searchParams]);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!token) {
      setError("This password reset link is invalid.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await authService.resetPassword(token, password);
      setIsComplete(true);
      setPassword("");
      setConfirmPassword("");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not reset your password.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title={isComplete ? "Password updated" : "Choose a new password"}
      subtitle={
        isComplete
          ? "Your Veya password has been reset successfully."
          : "Use a new password that you don’t use elsewhere."
      }
      footer={<Link to="/login">Back to sign in</Link>}
    >
      {isComplete ? (
        <div className="auth-form">
          <div className="form-banner">
            Your password has been changed. Existing Veya sessions were signed out
            for security.
          </div>
          <Link className="primary-button auth-button-link" to="/login">
            Sign in with new password
          </Link>
        </div>
      ) : (
        <form className="auth-form" onSubmit={handleSubmit}>
          <FormField
            autoComplete="new-password"
            label="New password"
            minLength={8}
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            value={password}
          />

          <FormField
            autoComplete="new-password"
            label="Confirm new password"
            minLength={8}
            name="confirmPassword"
            onChange={(event) => setConfirmPassword(event.target.value)}
            type="password"
            value={confirmPassword}
          />

          {error ? (
            <div className="form-banner form-banner--error">{error}</div>
          ) : null}

          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Updating password…" : "Reset password"}
          </button>
        </form>
      )}
    </AuthLayout>
  );
}
