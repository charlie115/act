export default function BotPlaceholderPanel({ title, description }) {
  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Bot</p>
          <h1>{title}</h1>
        </div>
      </div>
      <div className="inline-note">{description}</div>
    </section>
  );
}
