const suggestions = [
  "Summarize my documents",
  "What is in my knowledge base?",
  "Search Wikipedia for India",
];

export function createSearchPanel(): string {
  return `
    <form class="search-form" id="search-form">
      <label class="sr-only" for="question">Ask a question</label>
      <input
        id="question"
        name="question"
        type="text"
        maxlength="2000"
        placeholder="What are the key points in my documents?"
        autocomplete="off"
        required
      />
      <button class="search-submit" type="submit">
        <span>Search</span><span aria-hidden="true">↗</span>
      </button>
    </form>
    <div class="suggestions" role="group" aria-label="Example questions">
      <span class="suggestion-label">TRY ASKING</span>
      ${suggestions
        .map(
          (suggestion) =>
            `<button class="suggestion-chip" type="button" data-question="${suggestion}">${suggestion}<span aria-hidden="true">↗</span></button>`,
        )
        .join("")}
    </div>
  `;
}
