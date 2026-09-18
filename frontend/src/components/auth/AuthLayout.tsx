import type { PropsWithChildren, ReactNode } from "react";
import { Link } from "react-router-dom";

type AuthLayoutProps = PropsWithChildren<{
  title: string;
  subtitle: string;
  footer?: ReactNode;
}>;

export function AuthLayout({
  title,
  subtitle,
  footer,
  children,
}: AuthLayoutProps) {
  return (
    <main className="auth-page">
      <section className="auth-brand">
        <Link className="brand-mark" to="/">
          VEYA
        </Link>
        <h1>Understand your audience without absorbing the negativity.</h1>
        <p>
          Turn social comments into clear, healthier insights for your content.
        </p>
      </section>

      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-card__header">
          <p className="auth-kicker">Welcome to Veya</p>
          <h2 id="auth-title">{title}</h2>
          <p>{subtitle}</p>
        </div>

        {children}

        {footer ? <div className="auth-card__footer">{footer}</div> : null}
      </section>
    </main>
  );
}
