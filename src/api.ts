/** A single matched contact. */
export interface Contact {
  first_name: string;
  last_name: string;
  city: string;
  state: string;
  phone: string;
  npa_id: string;
}

/** A summary of one or more contributions to a specific committee. */
export interface CommitteeSummary {
  name: string;
  party: string;
  total_cents: number;
  total_fmt: string;
  percent: number;
}

/** A summary of one or more contributions to a specific party. */
export interface PartySummary {
  total_cents: number;
  total_fmt: string;
  percent: number;
}

/** A summary of contributions by a single contact. */
export interface ContributionSummary {
  total_cents: number;
  total_fmt: string;
  committees: Record<string, CommitteeSummary>;
  parties: Record<string, PartySummary>;
}

/** A single search result. */
export interface SearchResult {
  contact: Contact;
  summary: ContributionSummary;
}

/** A successful search response. */
export interface SuccessSearchResponse {
  ok: true;
  results: SearchResult[];
}

/** An error response. */
export interface ErrorSearchResponse {
  ok: false;
  message: string;
  code: string;
}

/** A successful contact response. */
export type SearchResponse = SuccessSearchResponse | ErrorSearchResponse;

/** Comparator for two SearchResult instances. */
export const compareSearchResults = (
  a: SearchResult,
  b: SearchResult
): number => a.summary.total_cents - b.summary.total_cents;

/** Perform a search of a contact list. */
export const search = async (form: FormData): Promise<SearchResponse> => {
  // assert that there is a 'data' field in the form
  const dataField = form.get("data");
  if (!(dataField instanceof File)) {
    throw new Error("Invalid form data");
  }

  const response = await fetch("/api/search", {
    method: "POST",
    body: form,
  });
  const data = (await response.json()) as SearchResponse;
  if (!data.ok) {
    return data;
  }

  // sort the results by total contribution amount, from most to least
  // TODO: where *should* this go?
  const results = [...data.results].sort(compareSearchResults);
  results.reverse();
  return { ok: true, results };
};
