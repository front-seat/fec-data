# fec-data

Working with FEC individual contribution data

You'll want to download FEC's 2019-2020 dataset from here: https://www.fec.gov/data/browse-data/?tab=bulk-data
And you'll want to symlink `./data/indiv20.txt` to the `itcont.txt` file you download from FEC.

Details on the FEC data schema: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/

### Notes on installing dependencies locally on a Apple Silicon mac

We're using `python 3.12`. Modern Macs have `clang >= 15.x` (mine has `17.0.4`).

Alas, a transitive dependency (`multidict`) is currently broken in this environment and, also, does not ship binary wheels. Here's my solution: https://github.com/aio-libs/multidict/pull/877#issuecomment-1812948387

### Running locally

You'll need the sqlite databases, of course (ask Dave).

Then, you'll need to install the dependencies:

```
npm install
CFLAGS="-Wno-error=int-conversion" pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Then, you'll need to run both the Vite front-end server AND the python+litestar backend server:

```
./scripts/run.sh
```

Pop open http://localhost:2222/ and you should see the app.
