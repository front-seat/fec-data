import type { PartySummary, SearchResult, SuccessSearchResponse } from "../api";

import clsx from "clsx";

import {
  formatParty,
  formatPercent,
  formatUSD,
  partyColorClassName,
  toTitleCase,
} from "../utils/format";

/**
 * Create a copy of the `parties` structure. Count all non-UNK parties and get
 * the percentage total for each.
 *
 * Then, take the UNK party and distribute its total with the same percentage
 * breakdown as the other parties.
 *
 * If there is only one party, and it is UNK, leave it be.
 *
 * TODO: this belongs on the server
 */
const revisePartySummary = (
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

/** Return the identifier of the party with the largest percentage summary. */
const largestParty = (parties: Record<string, PartySummary>): string => {
  let largest = "UNK";
  let percent = 0;
  for (const [party, summary] of Object.entries(parties)) {
    if (summary.percent > percent) {
      largest = party;
      percent = summary.percent;
    }
  }
  return largest;
};

const SearchResults: React.FC<{ results: SearchResult[] }> = ({ results }) => (
  <div className="mt-8">
    <h2 className="font-bold text-2xl pb-4">Results</h2>
    <ul>
      {results.map((result, i) => (
        <li key={i} className="pb-4 border-b-2">
          <p
            className={clsx(
              "font-bold text-3xl",
              partyColorClassName(
                largestParty(revisePartySummary(result.summary.parties))
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
            {Object.entries(revisePartySummary(result.summary.parties)).map(
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

/** Top-level view component for showing successful search results. */
export const SearchResultsView: React.FC<{
  response: SuccessSearchResponse;
}> = ({ response }) => <SearchResults results={response.results} />;
