import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { AuthLayout } from "../components/auth/AuthLayout";
import { FormField } from "../components/auth/FormField";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim()) {
      return;
    }

    setSubmitted(true);
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your account email. Password-reset delivery will be enabled when the backend mailer flow is added."
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
          }}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />

        {submitted ? (
          <div className="form-banner">
            The reset screen is ready. Email delivery is not enabled yet because
            the backend forgot-password endpoint and mail provider still need to
            be implemented.
          </div>
        ) : null}

        <button className="primary-button" type="submit">
          Continue
        </button>
      </form>
    </AuthLayout>
  );
}
