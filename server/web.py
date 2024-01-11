import pathlib
import tempfile
import typing as t

from litestar import Litestar, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body

from server.data.contacts.abbu import ZipABBUManager
from server.data.contacts.google import GoogleContactExportManager
from server.data.manager import DataManager
from server.data.search import ContactContributionSearcher


@get("/")
async def frontend_root() -> dict:
    """Return the index."""
    return {"file": "index.html"}


@get("/{path:path}")
async def frontend(path: pathlib.Path) -> dict:
    """Return the index."""
    if path.suffix == "":
        path = path / "index.html"
    return {"file": str(path)}


@post("/api/search")
async def search(
    data: t.Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]
) -> dict:
    """Search a collection of contacts and summarize them."""
    is_zip = data.content_type == "application/zip"
    is_csv = data.content_type == "text/csv"
    if not (is_zip or is_csv):
        return {
            "ok": False,
            "message": "Invalid file type.",
            "code": "invalid_file_type",
        }
    content = await data.read()
    # Write to a temporary file; then pass it to the ZipABBUManager.
    # Be sure to clean up the temporary file when we're done.
    with tempfile.NamedTemporaryFile() as temp:
        temp.write(content)
        temp.flush()
        data_manager = DataManager.default()
        contact_manager = (
            ZipABBUManager(temp.name)
            if is_zip
            else GoogleContactExportManager(temp.name)
        )
        searcher = ContactContributionSearcher(data_manager)
        results = list(searcher.search_and_summarize_contacts(contact_manager))
        return {
            "ok": True,
            "results": [
                {
                    "contact": result[0].to_data(),
                    "summary": result[1].to_data() if result[1] else None,
                }
                for result in results
            ],
        }


app = Litestar([search, frontend, frontend_root])
