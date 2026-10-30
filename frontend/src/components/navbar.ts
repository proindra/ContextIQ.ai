export function createNavbar(): string {
  return `
    <header class="navbar">
      <a class="brand" href="/" aria-label="ContextIQ.ai home">
        contextiq.<span class="brand-ai">ai</span>
      </a>
      <div class="nav-actions">
        <button class="replay-button" id="hero-replay" type="button" aria-label="Replay hero animation">Replay <span aria-hidden="true">↻</span></button>
      </div>
    </header>
  `;
}
