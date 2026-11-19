export default function HomePage() {
  return (
    <main className="mila-main">
      <h1>Mila assistant</h1>
      <p>
        Auth modes: <code>unauthenticated</code> (retrieve blocked),{' '}
        <code>authenticated</code> (verified role), or <code>incognito</code>{' '}
        (<code>public</code> role). Top-bar Sign in, chat “sign me in”, or ask a
        knowledge question to be prompted. Dismiss → continue as incognito.
      </p>
    </main>
  );
}
