import React, { useCallback, useState } from "react";
import "./App.css";
import type { SearchResponse } from "./api";
import { search } from "./api";
import { SearchResultsView } from "./views/SearchResultsView";
import { UploadView } from "./views/UploadView";

const TenAgainstTrump: React.FC = () => {
  const [response, setResponse] = useState<SearchResponse | null>(null);

  const onSubmit = useCallback(async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    setResponse(await search(formData));
  }, []);

  return (
    <div>
      {response && response.ok ? (
        <SearchResultsView response={response} />
      ) : (
        <UploadView response={response} onSubmit={onSubmit} />
      )}
    </div>
  );
};

export default TenAgainstTrump;
