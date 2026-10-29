export function scrollToElement(
  element: HTMLElement,
  block: ScrollLogicalPosition = "start",
): void {
  const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
  element.scrollIntoView({ behavior, block });
}

export function setFormSubmitting(
  button: HTMLButtonElement,
  isSubmitting: boolean,
): void {
  button.disabled = isSubmitting;
  button.innerHTML = isSubmitting
    ? '<span class="button-spinner" aria-hidden="true"></span><span>Searching</span>'
    : '<span>Search</span><span aria-hidden="true">↗</span>';
}
