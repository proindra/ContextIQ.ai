export function setLoadingIndicator(
  container: HTMLElement,
  isLoading: boolean,
): void {
  container.setAttribute("aria-busy", String(isLoading));
  if (!isLoading) {
    container.replaceChildren();
    return;
  }

  container.innerHTML = `
    <div class="loading-card" role="status">
      <span class="loading-orb" aria-hidden="true"></span>
      <div>
        <strong>Thinking through your question</strong>
        <p>Searching your sources and gathering the best answer...</p>
      </div>
      <span class="loading-dots" aria-hidden="true"><i></i><i></i><i></i></span>
    </div>
  `;
}
