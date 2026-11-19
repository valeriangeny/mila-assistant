export default function HomePage() {
  return (
    <main className="mila-main">
      <h1>Mila assistant</h1>
      <p>
        Auth demos: top-bar <strong>Sign in</strong>, or in chat say “sign me
        in” / “switch user” for a card that redirects to the mock IdP (Alice /
        Priya / Marcus / Dana). The verified <code>role</code> is passed into
        the agent for retrieval filters.
      </p>
    </main>
  );
}
