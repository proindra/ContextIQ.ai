import type { SearchResponse, SourceDocument } from "../types/api";

function createSourceCard(source: SourceDocument, index: number): HTMLElement {
  const card = document.createElement("article");
  card.className = "source-card";

  const number = document.createElement("span");
  number.className = "source-number";
  number.textContent = String(index + 1).padStart(2, "0");

  const body = document.createElement("div");
  body.className = "source-body";
  const title = document.createElement("h4");
  title.textContent = source.title;
  const content = document.createElement("p");
  content.textContent = source.content;
  body.append(title, content);

  card.append(number, body);
  if (source.source?.startsWith("https://")) {
    const link = document.createElement("a");
    link.className = "source-link";
    link.href = source.source;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "↗";
    link.setAttribute("aria-label", `Open source: ${source.title}`);
    card.append(link);
  }

  return card;
}

export function renderAnswer(
  container: HTMLElement,
  result: SearchResponse,
): void {
  container.replaceChildren();
  container.className = "answer-panel result-enter";

  const heading = document.createElement("div");
  heading.className = "answer-heading";
  heading.innerHTML = `
    <span class="eyebrow"><span class="status-dot"></span> YOUR ANSWER</span>
    <span class="response-time">${result.elapsed_seconds.toFixed(2)}s</span>
  `;

  const question = document.createElement("h2");
  question.className = "answer-question";
  question.textContent = result.question;

  const answer = document.createElement("p");
  answer.className = "answer-copy";
  answer.textContent = result.answer;

  const answerCard = document.createElement("article");
  answerCard.className = "answer-card";
  answerCard.append(heading, question, answer);
  container.append(answerCard);

  if (result.sources.length > 0) {
    const sourcesSection = document.createElement("section");
    sourcesSection.className = "sources-section";
    const sourcesHeading = document.createElement("div");
    sourcesHeading.className = "sources-heading";
    sourcesHeading.innerHTML = `
      <div><span class="eyebrow">GROUNDED IN</span><h3>Source passages</h3></div>
      <span class="source-count">${result.sources.length} sources</span>
    `;
    const list = document.createElement("div");
    list.className = "sources-list";
    result.sources.forEach((source, index) => {
      list.append(createSourceCard(source, index));
    });
    sourcesSection.append(sourcesHeading, list);
    container.append(sourcesSection);
  }
}

export function renderSearchError(
  container: HTMLElement,
  message: string,
): void {
  container.replaceChildren();
  container.className = "answer-panel result-enter";
  const error = document.createElement("div");
  error.className = "error-card";
  error.setAttribute("role", "alert");
  const title = document.createElement("strong");
  title.textContent = "We couldn't complete that search";
  const detail = document.createElement("p");
  detail.textContent = message;
  error.append(title, detail);
  container.append(error);
}
