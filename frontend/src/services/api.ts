import type {
  ApiErrorResponse,
  SearchRequest,
  SearchResponse,
} from "../types/api";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

function isApiError(payload: unknown): payload is ApiErrorResponse {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "detail" in payload &&
    typeof payload.detail === "string"
  );
}

function isSearchResponse(payload: unknown): payload is SearchResponse {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }
  const result = payload as Record<string, unknown>;
  return (
    typeof result.question === "string" &&
    typeof result.answer === "string" &&
    typeof result.elapsed_seconds === "number" &&
    Array.isArray(result.sources) &&
    result.sources.every(
      (source) =>
        typeof source === "object" &&
        source !== null &&
        "title" in source &&
        typeof source.title === "string" &&
        "content" in source &&
        typeof source.content === "string" &&
        "source" in source &&
        (typeof source.source === "string" || source.source === null),
    )
  );
}

export async function searchDocuments(
  request: SearchRequest,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = isApiError(payload)
      ? payload.detail
      : `Search failed (${response.status}). Please try again.`;
    throw new Error(detail);
  }

  if (!isSearchResponse(payload)) {
    throw new Error("The API returned an invalid search response.");
  }

  return payload;
}
