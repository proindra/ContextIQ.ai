import "./style.css";
import { renderAnswer, renderSearchError } from "./components/answer-panel";
import { setLoadingIndicator } from "./components/loading-indicator";
import { createNavbar } from "./components/navbar";
import { createSearchPanel } from "./components/search-panel";
import { searchDocuments } from "./services/api";
import { initializeHeroMotion } from "./animations/hero";
import { initializeScrollReveal } from "./animations/scroll";
import { scrollToElement, setFormSubmitting } from "./animations/transitions";

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) {
  throw new Error("The application root element was not found.");
}

function scrambleWord(word: string): string {
  return [...word]
    .map(
      (letter) =>
        `<span class="ch" data-final="${letter}">${letter}</span>`,
    )
    .join("");
}

app.innerHTML = `
  <div class="notice-banner">ContextIQ.ai now searches your PDFs and the web in one question.</div>
  ${createNavbar()}
  <main>
    <section class="hero" id="hero">
      <div class="hero-content">
        <div class="hero-copy">
          <h1 aria-label="Search anything">
            <span class="row" aria-hidden="true">
              <span class="pin" id="pin">
                <svg viewBox="-50 -50 100 100"><g id="pinG">
                  <path d="M0 0 C-4 -24 -20 -38 -42 -34 C-40 -12 -22 -2 0 0Z" fill="var(--pink)"/>
                  <path d="M0 0 C24 -4 38 -20 34 -42 C12 -40 2 -22 0 0Z" fill="var(--orange)"/>
                  <path d="M0 0 C4 24 20 38 42 34 C40 12 22 2 0 0Z" fill="var(--purple)"/>
                  <path d="M0 0 C-24 4 -38 20 -34 42 C-12 40 -2 22 0 0Z" fill="var(--green)"/>
                </g></svg>
              </span>
              ${scrambleWord("Se")}
              <span class="ico" id="ast"><svg viewBox="-50 -50 100 100"><g id="astG" stroke="var(--pink)" stroke-width="13" stroke-linecap="round"><path d="M0 -40V40"/><path d="M-35 -20L35 20"/><path d="M-35 20L35 -20"/></g></svg></span>
              ${scrambleWord("rch")}
            </span>
            <span class="row two" aria-hidden="true">
              ${scrambleWord("any")}
              <span class="ico" id="bolt"><svg viewBox="-50 -50 100 100"><path id="boltP" d="M14 -46L-26 6H-2L-12 46L28 -8H4Z" fill="var(--green)" stroke="var(--green)" stroke-width="4" stroke-linejoin="round"/></svg></span>
              ${scrambleWord("thing")}
            </span>
          </h1>
          <div class="hero-tag" id="tag">
            <div class="hero-brace">
              <b aria-hidden="true">{</b>
              <p>Ask a question. An agent reads your documents and Wikipedia, then answers with the source passages.</p>
              <b aria-hidden="true">}</b>
            </div>
            <button class="hero-cta" id="hero-cta" type="button">Start searching</button>
          </div>
        </div>
      </div>
    </section>

    <section class="search-section" id="search">
      <div class="search-section-inner">
        <span class="eyebrow">YOUR NEXT QUESTION</span>
        <h2>What would you like to find?</h2>
        <p class="search-intro">Search your documents and Wikipedia, then explore the answer and its sources.</p>
        <div class="hero-search">${createSearchPanel()}</div>
        <p class="hero-hint">Hover the letters. A few rescramble on their own.</p>
      </div>
    </section>

    <section class="workspace-section" aria-label="Search results">
      <div id="loading-mount" class="loading-mount"></div>
      <div id="answer-mount" class="answer-panel" aria-live="polite"></div>
    </section>

    <section class="how-section">
      <div class="how-heading" data-reveal>
        <span class="eyebrow">INTELLIGENCE, WITH CONTEXT</span>
        <h2>More than a search.<br /><span>A thought partner.</span></h2>
      </div>
      <div class="steps-grid">
        <article class="step-card" data-reveal>
          <span class="step-number">01</span><span class="step-symbol">⌕</span>
          <h3>Find the signal</h3>
          <p>Your question is matched to relevant passages from the knowledge base.</p>
          <span class="step-tag">FAISS · SEMANTIC RETRIEVAL</span>
        </article>
        <article class="step-card step-card-accent" data-reveal>
          <span class="step-number">02</span><span class="step-symbol">✳</span>
          <h3>Follow the thread</h3>
          <p>A ReAct agent can search your documents or look up general facts on Wikipedia.</p>
          <span class="step-tag">LANGGRAPH · TOOL USE</span>
        </article>
        <article class="step-card" data-reveal>
          <span class="step-number">03</span><span class="step-symbol">↗</span>
          <h3>See the whole picture</h3>
          <p>Get a clear answer alongside the source passages that informed it.</p>
          <span class="step-tag">GROUNDED · TRACEABLE</span>
        </article>
      </div>
    </section>
  </main>
  <footer class="footer">
    <a class="brand footer-brand" href="/">contextiq.<span class="brand-ai">ai</span></a>
  </footer>
`;

const form = document.querySelector<HTMLFormElement>("#search-form");
const questionInput = document.querySelector<HTMLInputElement>("#question");
const submitButton = form?.querySelector<HTMLButtonElement>('button[type="submit"]');
const loadingMount = document.querySelector<HTMLElement>("#loading-mount");
const answerMount = document.querySelector<HTMLElement>("#answer-mount");
const replayButton = document.querySelector<HTMLButtonElement>("#hero-replay");
const heroCta = document.querySelector<HTMLButtonElement>("#hero-cta");
const hero = document.querySelector<HTMLElement>("#hero");

if (
  !form ||
  !questionInput ||
  !submitButton ||
  !loadingMount ||
  !answerMount ||
  !replayButton ||
  !heroCta ||
  !hero
) {
  throw new Error("The search interface could not be initialized.");
}

heroCta.addEventListener("click", () => {
  const searchSection = document.querySelector<HTMLElement>("#search");
  if (!searchSection) {
    throw new Error("The search section could not be found.");
  }
  scrollToElement(searchSection);
  questionInput.focus({ preventScroll: true });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) {
    questionInput.focus();
    return;
  }

  setFormSubmitting(submitButton, true);
  answerMount.replaceChildren();
  setLoadingIndicator(loadingMount, true);
  scrollToElement(loadingMount);
  try {
    const result = await searchDocuments({ question });
    setLoadingIndicator(loadingMount, false);
    renderAnswer(answerMount, result);
  } catch (error) {
    setLoadingIndicator(loadingMount, false);
    renderSearchError(
      answerMount,
      error instanceof Error ? error.message : "An unexpected error occurred.",
    );
  } finally {
    setFormSubmitting(submitButton, false);
  }
});

document.querySelectorAll<HTMLButtonElement>("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question ?? "";
    form.requestSubmit();
  });
});

initializeHeroMotion(hero, replayButton);
initializeScrollReveal();
