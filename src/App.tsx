import clsx from "clsx";
import React, { useCallback, useState } from "react";
import "./App.css";

interface Contact {
  first_name: string;
  last_name: string;
  city: string;
  state: string;
  phone: string;
  npa_id: string;
}

interface CommitteeSummary {
  name: string;
  party: string;
  total_cents: number;
  total_fmt: string;
  percent: number;
}

interface PartySummary {
  total_cents: number;
  total_fmt: string;
  percent: number;
}

interface ContributionSummary {
  total_cents: number;
  total_fmt: string;
  committees: Record<string, CommitteeSummary>;
  parties: Record<string, PartySummary>;
}

interface SearchResult {
  contact: Contact;
  summary: ContributionSummary;
}

interface SuccessSearchResponse {
  ok: true;
  results: SearchResult[];
}

interface ErrorSearchResponse {
  ok: false;
  message: string;
  code: string;
}

const formatPercent = (percent: number): string =>
  `${(percent * 100).toFixed(1)}%`;

const formatUSD = (cents: number): string =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);

const formatParty = (party: string): string => {
  switch (party) {
    case "DEM":
      return "Democrat";
    case "REP":
      return "Republican";
    case "IND":
      return "Independent";
    case "OTH":
      return "Other";
    case "UNK":
      return "Unknown";
    default:
      return party;
  }
};

const partyBreakdownColorClassName = (
  parties: Record<string, PartySummary>
): string => {
  const party = Object.entries(parties).sort(
    ([, a], [, b]) => b.total_cents - a.total_cents
  )[0][0];
  switch (party) {
    case "DEM":
      return "text-blue-800";
    case "REP":
      return "text-red-800";
    case "IND":
      return "text-yellow-800";
    default:
      return "text-gray-800";
  }
};

/**
 * Create a copy of the `parties` structure. Count all non-UNK parties and get
 * the percentage total for each.
 *
 * Then, take the UNK party and distribute its total with the same percentage
 * breakdown as the other parties.
 *
 * If there is only one party, and it is UNK, leave it be.
 */
const revisePartyBreakdown = (
  parties: Record<string, PartySummary>
): Record<string, PartySummary> => {
  const nonUnknownParties = Object.entries(parties).filter(
    ([party]) => party !== "UNK"
  );
  if (nonUnknownParties.length === 0) {
    return parties;
  }
  if (nonUnknownParties.length === Object.entries(parties).length) {
    return parties;
  }
  const totalUnknown = parties.UNK.total_cents;
  const revisedParties: Record<string, PartySummary> = {};
  for (const [party, summary] of nonUnknownParties) {
    revisedParties[party] = {
      ...summary,
      total_cents: summary.total_cents + totalUnknown * summary.percent,
      total_fmt: formatUSD(
        summary.total_cents + totalUnknown * summary.percent
      ),
    };
  }
  // Fix the percentages
  const revisedTotal = Object.values(revisedParties).reduce(
    (total, summary) => total + summary.total_cents,
    0
  );
  for (const [party, summary] of Object.entries(revisedParties)) {
    revisedParties[party] = {
      ...summary,
      percent: summary.total_cents / revisedTotal,
    };
  }
  return revisedParties;
};

type SearchResponse = SuccessSearchResponse | ErrorSearchResponse;

const compareSearchResults = (a: SearchResult, b: SearchResult): number =>
  a.summary.total_cents - b.summary.total_cents;

const reverseCompareSearchResults = (a: SearchResult, b: SearchResult) =>
  compareSearchResults(b, a);

const toTitleCase = (s: string): string =>
  s
    .toLowerCase()
    .replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substring(1));

const SearchResults: React.FC<{ results: SearchResult[] }> = ({ results }) => (
  <div className="mt-8">
    <h2 className="font-bold text-2xl pb-4">Results</h2>
    <ul>
      {results.map((result, i) => (
        <li key={i} className="pb-4 border-b-2">
          <p
            className={clsx(
              "font-bold text-3xl",
              partyBreakdownColorClassName(
                revisePartyBreakdown(result.summary.parties)
              )
            )}
          >
            {toTitleCase(
              `${result.contact.first_name} ${result.contact.last_name}`
            )}
          </p>
          <p>
            {toTitleCase(result.contact.city)}, {result.contact.state}
          </p>
          {/* <p>{result.contact.phone}</p> */}
          <p>Total: {result.summary.total_fmt}</p>
          {/* Produce a party breakdown */}
          <ul>
            {Object.entries(revisePartyBreakdown(result.summary.parties)).map(
              ([party, partySummary]) => (
                <li key={party}>
                  <p className="font-bold text-lg">
                    {formatParty(party)}: {partySummary.total_fmt} (
                    {formatPercent(partySummary.percent)})
                  </p>
                </li>
              )
            )}
          </ul>
          {/* <ul>
            {Object.entries(result.summary.committees).map(
              ([committeeId, committee]) => (
                <li key={committeeId}>
                  <p className="font-bold text-lg">{committee.name}</p>
                  <p>
                    {committee.total_fmt} ({formatPercent(committee.percent)})
                  </p>
                </li>
              )
            )}
          </ul> */}
        </li>
      ))}
    </ul>
  </div>
);

const SearchError: React.FC<{ message: string; code: string }> = ({
  message,
  code,
}) => (
  <div className="mt-8">
    <h2 className="font-bold text-2xl pb-4">Error</h2>
    <p>
      {message} ({code})
    </p>
  </div>
);

const SearchResponse: React.FC<{ searchResponse: SearchResponse }> = ({
  searchResponse,
}) =>
  searchResponse.ok ? (
    <SearchResults results={searchResponse.results} />
  ) : (
    <SearchError message={searchResponse.message} code={searchResponse.code} />
  );

function App() {
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(
    null
  );

  const onSubmit = useCallback(async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // post to /api/search as multi-part; get the JSON response back
    const formData = new FormData(e.currentTarget);
    const response = await fetch("/api/search", {
      method: "POST",
      body: formData,
    });
    const data = (await response.json()) as SearchResponse;
    if (!data.ok) {
      setSearchResponse(data);
    } else {
      const results = [...data.results].sort(reverseCompareSearchResults);
      setSearchResponse({
        ok: true,
        results,
      });
    }
  }, []);

  return (
    <div>
      <h1 className="font-bold text-4xl pb-8">TenForTrump</h1>
      <p>Export your Apple or GMail contacts and upload them here.</p>
      <form onSubmit={onSubmit} encType="multipart/form-data">
        <input
          type="file"
          id="data"
          name="data"
          className="mt-8 border-2 border-gray-200 p-2 rounded-md bg-gray-50"
        />
        <button
          type="submit"
          className="mt-8 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Do the thing
        </button>
      </form>
      {searchResponse && <SearchResponse searchResponse={searchResponse} />}
    </div>
  );
}

export default App;
