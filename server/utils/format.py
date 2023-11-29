def fmt_usd(cents: int) -> str:
    """Format a value in cents as USD."""
    return f"${cents / 100:,.2f}"
