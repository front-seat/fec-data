import type { ErrorSearchResponse } from "../api";

export interface UploadViewProps {
  response: ErrorSearchResponse | null;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}

export const UploadView: React.FC<UploadViewProps> = ({
  onSubmit,
  response,
}) => {
  return (
    <div>
      <form onSubmit={onSubmit}>
        <label htmlFor="file">Upload a file:</label>
        <input
          type="file"
          name="data"
          id="data"
          accept="application/zip,text/csv"
        />
        <button type="submit">Do the thing</button>
      </form>
      {response && <div>Error: {response.message}</div>}
    </div>
  );
};
