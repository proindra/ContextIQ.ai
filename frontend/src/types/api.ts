export interface SearchRequest {
  question: string;
}

export interface SourceDocument {
  title: string;
  source: string | null;
  content: string;
}

export interface SearchResponse {
  question: string;
  answer: string;
  sources: SourceDocument[];
  elapsed_seconds: number;
}

export interface ApiErrorResponse {
  detail?: string;
}
