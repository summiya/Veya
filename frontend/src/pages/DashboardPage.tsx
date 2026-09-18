import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const cards = [
  { label: "Positive", value: "74%", icon: "❤️" },
  { label: "Neutral", value: "17%", icon: "😐" },
  { label: "Negative", value: "6%", icon: "⚠️" },
  { label: "Toxic filtered", value: "3%", icon: "🛡️" },
];

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <main className="page">
      <header className="dashboard-header">
        <div>
          <span className="eyebrow">VEYA</span>
          <p className="muted">{user?.email}</p>
        </div>
        <button
          className="secondary-button"
          onClick={() => void handleLogout()}
          type="button"
        >
          Log out
        </button>
      </header>

      <section className="hero">
        <h1>Understand your audience without absorbing the negativity.</h1>
        <p>
          A creator-focused sentiment dashboard for turning social comments into
          healthier, useful insights.
        </p>
      </section>

      <section className="panel">
        <div>
          <p className="muted">Profile positivity</p>
          <strong className="score">74%</strong>
        </div>
        <div className="grid">
          {cards.map((card) => (
            <article className="card" key={card.label}>
              <span>{card.icon}</span>
              <strong>{card.value}</strong>
              <small>{card.label}</small>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
