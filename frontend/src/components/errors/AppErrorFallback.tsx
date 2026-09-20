export function AppErrorFallback() {
  return (
    <main className="app-error-page" role="alert">
      <section>
        <p className="auth-kicker">Veya</p>
        <h1>Something went wrong</h1>
        <p>
          We recorded the problem without sending your passwords, tokens, or
          private request data. Refresh the page to try again.
        </p>
        <button
          className="primary-button"
          onClick={() => window.location.reload()}
          type="button"
        >
          Refresh Veya
        </button>
      </section>
    </main>
  );
}
