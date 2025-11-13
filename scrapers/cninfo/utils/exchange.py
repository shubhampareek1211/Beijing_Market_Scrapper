def map_exchange_by_code(code: str):
    """
    Returns (exchange, board)
    Exchange in {"SSE","SZSE","BSE"}.
    Board examples: {"Main","SME","ChiNext","STAR","BSE主板"}.

    Per PDF requirements:
    - SSE 688xxx → STAR (科创板)
    - SZSE 300xxx → ChiNext (创业板)
    - SZSE 000xxx → Main
    - SZSE 002xxx → SME (small/medium enterprise)
    - BSE 43/83/87/88/89 → BSE主板
    """
    c = str(code).strip()
    if not c or not c.isdigit():
        return None, None

    # ----- Shanghai Stock Exchange (SSE) -----
    if c.startswith(("600", "601", "603", "605")):
        return "SSE", "Main"
    if c.startswith(("688", "689")):
        return "SSE", "STAR"  # 科创板
    if c.startswith("900"):  # B-shares
        return "SSE", "Main"

    # ----- Shenzhen Stock Exchange (SZSE) -----
    if c.startswith(("000", "001")):
        return "SZSE", "Main"
    if c.startswith("002"):
        return "SZSE", "SME"  # Small-Medium Enterprise board
    if c.startswith("003"):
        return "SZSE", "Main"
    if c.startswith("200"):  # B-shares
        return "SZSE", "Main"
    if c.startswith(("300", "301")):
        return "SZSE", "ChiNext"  # 创业板

    # ----- Beijing Stock Exchange (BSE) -----
    # BSE codes: 43xxxx, 83xxxx, 87xxxx, 88xxxx, 89xxxx
    if c.startswith(("430", "43")):
        return "BSE", "BSE主板"
    if c.startswith(("830", "831", "832", "833", "835", "836", "837", "838", "839", "83")):
        return "BSE", "BSE主板"
    if c.startswith(("870", "871", "872", "873", "875", "876", "877", "878", "87")):
        return "BSE", "BSE主板"
    if c.startswith(("880", "881", "882", "883", "884", "885", "886", "887", "888", "889", "88")):
        return "BSE", "BSE主板"
    if c.startswith("89"):
        return "BSE", "BSE主板"

    # Unknown pattern
    return None, None


def map_board_by_code(code: str, exchange: str = None) -> str:
    """
    Best-effort board detection from code pattern.

    Per PDF requirements:
    - SSE STAR: 688/689 → STAR
    - SZSE ChiNext: 300/301 → ChiNext
    - SZSE SME: 002 → SME (if we want to distinguish from Main)
    - BSE: 43/83/87/88/89 → BSE主板
    - Otherwise: Main

    Args:
        code: 6-digit stock code
        exchange: Optional exchange hint (SSE/SZSE/BSE)

    Returns:
        Board name string
    """
    c = (code or "").strip()

    # SSE boards
    if c.startswith(("688", "689")):
        return "STAR"  # 科创板

    # SZSE boards
    if c.startswith(("300", "301")):
        return "ChiNext"  # 创业板
    if c.startswith("002"):
        return "SME"  # Small-Medium Enterprise

    # BSE boards (all variations)
    bse_prefixes = (
        "43", "830", "831", "832", "833", "835", "836", "837", "838", "839",
        "870", "871", "872", "873", "875", "876", "877", "878",
        "880", "881", "882", "883", "884", "885", "886", "887", "888", "889"
    )
    if c.startswith(bse_prefixes):
        return "BSE主板"

    # Fallback: if exchange is explicitly BSE
    if (exchange or "").upper() == "BSE":
        return "BSE主板"

    # Default
    return "Main"


def normalize_exchange_code(raw_exchange: str) -> str:
    """
    Normalize various exchange representations to standard codes.

    Args:
        raw_exchange: Raw exchange string (e.g., "上交所", "SSE", "Shanghai")

    Returns:
        Normalized exchange code: SSE, SZSE, or BSE
    """
    if not raw_exchange:
        return None

    s = str(raw_exchange).strip().upper()

    # Shanghai
    if any(x in s for x in ["SSE", "SHANGHAI", "上交", "上海"]):
        return "SSE"

    # Shenzhen
    if any(x in s for x in ["SZSE", "SHENZHEN", "深交", "深圳"]):
        return "SZSE"

    # Beijing
    if any(x in s for x in ["BSE", "BEIJING", "北交", "北京"]):
        return "BSE"

    return None


def get_share_class(code: str) -> str:
    """
    Determine share class (A or B) from stock code.

    B-shares:
    - SSE: 900xxx
    - SZSE: 200xxx

    All others are A-shares.
    """
    c = str(code).strip()

    if c.startswith("200"):  # SZSE B-share
        return "B"
    if c.startswith("900"):  # SSE B-share
        return "B"

    return "A"