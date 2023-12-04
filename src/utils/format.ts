/** Convert a string to title case. */
export const toTitleCase = (s: string): string =>
  s
    .toLowerCase()
    .replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substring(1));

/** Format a number as a percentage. */
export const formatPercent = (percent: number, places: number = 1): string =>
  `${(percent * 100).toFixed(places)}%`;

/** Format a number as a dollar amount. */
export const formatUSD = (cents: number, fractionDigits: number = 0): string =>
  // format without cents.
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(cents / 100);

/** Format a party abbreviation as a full party name. */
export const formatParty = (party: string): string => {
  // see https://www.fec.gov/campaign-finance-data/party-code-descriptions/
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

/** Return a tailwind color class name for a party. */
export const partyColorClassName = (party: string) => {
  switch (party) {
    case "DEM":
      return "text-blue-800";
    case "REP":
      return "text-red-800";
    case "IND":
      return "text-cyan-800";
    default:
      return "text-gray-800";
  }
};
