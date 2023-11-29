import "./App.css";

function App() {
  return (
    <div>
      <h1 className="font-bold text-4xl pb-8">TenForTrump</h1>
      <p>Upload your contacts.zip file here:</p>
      <form action="/search" method="post" encType="multipart/form-data">
        <input
          type="file"
          id="contacts"
          className="mt-8 border-2 border-gray-200 p-2 rounded-md bg-gray-50"
        />
      </form>
    </div>
  );
}

export default App;
