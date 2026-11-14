const capabilities = [
  {
    title: "Patient workspace",
    description: "A secure place for patients to organize health information and prepare for care.",
  },
  {
    title: "Clinician workspace",
    description: "A review-oriented workspace for authorized clinical teams and source-linked drafts.",
  },
  {
    title: "Evidence-aware assistance",
    description: "Future medical explanations will be grounded in approved sources and clearly show uncertainty.",
  },
];

export default function Home() {
  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="SmartDoctor home">
          <span className="brand-mark" aria-hidden="true">+</span>
          <span>SmartDoctor</span>
        </a>
        <span className="environment-label">Development foundation</span>
      </header>
      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">PATIENT + CLINICIAN PLATFORM</p>
        <h1 id="hero-title">Health information, organized around better care.</h1>
        <p className="hero-copy">
          SmartDoctor is being built as a secure workspace for patient-provided records,
          authorized clinical information, and clinician-reviewed assistance.
        </p>
        <p className="notice" role="note">
          This development preview is not a medical service. It does not diagnose, prescribe,
          or replace advice from a qualified healthcare professional. For an emergency,
          contact local emergency services.
        </p>
      </section>
      <section className="capability-grid" aria-label="Planned platform capabilities">
        {capabilities.map((item, index) => (
          <article className="capability-card" key={item.title}>
            <span className="card-index">0{index + 1}</span>
            <h2>{item.title}</h2>
            <p>{item.description}</p>
          </article>
        ))}
      </section>
      <footer className="footer">
        <span>SmartDoctor · Early development</span>
        <span>No real patient data in development</span>
      </footer>
    </main>
  );
}
