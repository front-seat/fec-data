from litestar import Litestar, get

from server.data.contacts import Contact
from server.data.manager import DataManager
from server.data.models import get_engine
from server.data.nicknames import NicknamesManager
from server.data.summaries import ContributionSummaryManager


@get("/")
async def index() -> dict:
    """Return the index."""
    return {"message": "Hello, world!"}


@get("/summarize", sync_to_thread=True)
def summarize() -> dict:
    """Summarize somebody."""
    data_manager = DataManager.default()
    nicknames_manager = NicknamesManager.from_data_manager(data_manager)
    engine = get_engine(data_manager, "WA")
    contact = Contact("MICHAEL", "MATHIEU", "SEATTLE", "WA", None)
    summary_manager = ContributionSummaryManager(engine, nicknames_manager)
    summary = summary_manager.preferred_summary_for_contact(contact)
    return summary.to_data() if summary else {}


app = Litestar([index, summarize])
