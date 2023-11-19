"""Tools for working with all raw data files."""


# CONSIDER: the FEC publishes what amounts to a relational dataset, and I
# originally considered just dumping stuff into a massive SQLite database.
# But then I got hooked on summarizing, and building fuzzy identifiers, and
# the code took a different form. In retrospect, the existence of IGetNicknameIndex
# and IGetCommittee just screams "dude, you shoulda used SQLAlchemy and done
# some ETL on the inbound side to slim it down".
#
# So this comment asks me to revisit this, and consider it a TODO.
