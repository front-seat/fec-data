# fec-data

Working with FEC individual contribution data

You'll want to download FEC's 2019-2020 dataset from here: https://www.fec.gov/data/browse-data/?tab=bulk-data
And you'll want to symlink `./data/indiv20.txt` to the `itcont.txt` file you download from FEC.

Details on the FEC data schema: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/

### Notes on installing dependencies locally on a Apple Silicon mac

We're using `python 3.12`. Modern Macs have `clang >= 15.x` (mine has `17.0.4`).

Alas, a transitive dependency (`multidict`) is currently broken in this environment and, also, does not ship binary wheels. Here's my solution: https://github.com/aio-libs/multidict/pull/877#issuecomment-1812948387
