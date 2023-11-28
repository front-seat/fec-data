class ContributionColumns:
    """
    Column indices for the individual contribution master file.

    See:
    https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
    """

    COMMITTEE_ID = 0  # Filer identification number (CMTE_ID)
    AMENDMENT_INDICATOR = 1  # AMNDT_IND
    REPORT_TYPE = 2  # RPT_TP
    PRIMARY_GENERAL_INDICATOR = 3  # TRANSACTION_PGI
    IMAGE_NUMBER = 4  # IMAGE_NUM
    TRANSACTION_TYPE = 5  # TRANSACTION_TP
    ENTITY_TYPE = 6  # ENTITY_TP (see EntityTypeCode)
    NAME = 7  # NAME (of the contributor, typically in LAST, FIRST <MIDDLE> format)
    CITY = 8  # CITY
    STATE = 9  # STATE
    ZIP_CODE = 10  # ZIP_CODE (usually 5 or 9 digits, but there are lots of odd ones)
    EMPLOYER = 11  # EMPLOYER
    OCCUPATION = 12  # OCCUPATION
    TRANSACTION_DATE = 13  # TRANSACTION_DT (MMDDYYYY)
    TRANSACTION_AMOUNT = 14  # TRANSACTION_AMT (in dollars, NUMBER(14, 2))
    OTHER_ID = 15  # OTHER_ID (for non-individual contributions)
    TRANSACTION_ID = 16  # TRAN_ID
    FILE_NUMBER = 17  # FILE_NUM
    MEMO_CODE = 18  # MEMO_CD
    MEMO_TEXT = 19  # MEMO_TEXT
    SUB_ID = 20  # SUB_ID (FEC record ID)


class EntityTypeCode:
    CANDIDATE = "CAN"
    CANDIDATE_COMMITTEE = "CCM"
    COMMITTEE = "COM"
    INDIVIDUAL = "IND"
    ORGANIZATION = "ORG"
    PAC = "PAC"
    PARTY_ORGANIZATION = "PTY"

    @classmethod
    def name_for_code(cls, code: str) -> str | None:
        """Return the name for the given entity type code."""
        for attr in dir(EntityTypeCode):
            if not attr.startswith("__"):
                if getattr(EntityTypeCode, attr) == code:
                    return attr.replace("_", " ").title()
        return None


class CommitteeColumns:
    """
    Column indices for the committee master file.

    See:
    https://www.fec.gov/campaign-finance-data/committee-master-file-description/
    """

    ID = 0  # CMTE_ID
    NAME = 1  # CMTE_NM
    TREASURER_NAME = 2  # TRES_NM
    STREET_1 = 3  # CMTE_ST1
    STREET_2 = 4  # CMTE_ST2
    CITY = 5  # CMTE_CITY
    STATE = 6  # CMTE_ST
    ZIP_CODE = 7  # CMTE_ZIP
    DESIGNATION = 8  # CMTE_DSGN
    TYPE = 9  # CMTE_TP
    PARTY = 10  # CMTE_PTY_AFFILIATION
    ORG_TYPE = 11  # ORG_TP
    CONNECTED_ORG_NAME = 12  # CONNECTED_ORG_NM
    CANDIDATE_ID = 13  # CAND_ID


class Party:
    """
    Political party codes.

    For an (incredibly) exhaustive list, see:
    https://www.fec.gov/campaign-finance-data/party-code-descriptions/
    """

    REPUBLICAN = "REP"
    DEMOCRAT = "DEM"
    INDEPENDENT = "IND"
    LIBERTARIAN = "LIB"
    GREEN = "GRE"
    UNKNOWN = "UNK"  # We specifically ignore this/convert to None

    @classmethod
    def name_for_code(cls, code: str) -> str | None:
        """Return the name for the given party code."""
        for attr in dir(Party):
            if not attr.startswith("__"):
                if getattr(Party, attr) == code:
                    return attr.title()
        return None
