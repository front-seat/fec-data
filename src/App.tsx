import React, { useCallback, useState } from "react";
import "./App.css";
import type { SearchResponse } from "./api";
import { search } from "./api";
import { Chrome } from "./components/Chrome";
import { Hero } from "./components/Hero";
import { SearchResultsView } from "./views/SearchResultsView";
import { UploadView } from "./views/UploadView";

const NotStarted: React.FC<{ onGetStarted: () => void }> = ({
  onGetStarted,
}) => <Hero onGetStarted={onGetStarted} />;

const Started: React.FC<{
  response: SearchResponse | null;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}> = ({ response, onSubmit }) => (
  <div>
    {response && response.ok ? (
      <SearchResultsView response={response} />
    ) : (
      <UploadView response={response} onSubmit={onSubmit} />
    )}
  </div>
);

const TenAgainstTrump: React.FC = () => {
  const [started, setStarted] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  const onSubmit = useCallback(async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    setResponse(await search(formData));
  }, []);

  return (
    <Chrome>
      {started ? (
        <Started response={response} onSubmit={onSubmit} />
      ) : (
        <NotStarted onGetStarted={() => setStarted(true)} />
      )}
    </Chrome>
  );
};

export default TenAgainstTrump;
