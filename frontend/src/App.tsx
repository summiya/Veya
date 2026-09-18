const cards = [
  { label: "Positive", value: "74%", icon: "❤️" },
  { label: "Neutral", value: "17%", icon: "😐" },
  { label: "Negative", value: "6%", icon: "⚠️" },
  { label: "Toxic filtered", value: "3%", icon: "🛡️" },
];

export default function App() {
  return (
    <main className="page">
      <section className="hero">
        <span className="eyebrow">VEYA</span>
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
