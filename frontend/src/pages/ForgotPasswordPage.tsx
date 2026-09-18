import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { AuthLayout } from "../components/auth/AuthLayout";
import { FormField } from "../components/auth/FormField";
import { ApiError } from "../lib/api";
import { authService } from "../services/auth-service";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!email.trim()) {
      setError("Enter your email address.");
      return;
    }

    setIsSubmitting(true);

    try {
      await authService.forgotPassword(email.trim());
      setSubmitted(true);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not process your password reset request.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your Veya account email and we’ll send you a secure reset link."
      footer={<Link to="/login">Back to sign in</Link>}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <FormField
          autoComplete="email"
          label="Email"
          name="email"
          onChange={(event) => {
            setEmail(event.target.value);
            setSubmitted(false);
            setError("");
          }}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />

        {submitted ? (
          <div className="form-banner">
            If an active Veya account exists for that email, we sent a password
            reset link. Check your inbox and spam folder.
          </div>
        ) : null}

        {error ? (
          <div className="form-banner form-banner--error">{error}</div>
        ) : null}

        <button className="primary-button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Sending…" : "Send reset link"}
        </button>
      </form>
    </AuthLayout>
  );
}
