"""마켓 분류 함수 및 TAG_IDS 상수.

블랙리스트 우선 → 화이트리스트 로직.
상수는 Spike LEARNINGS (spikes/polymarket-tags/LEARNINGS.md) 기반.
"""
from src.modules.market.domain.models import Classification


# 스포츠 + 엔터테인먼트 + 개인 태그. 엄격 (100% 확실한 비매크로만).
NON_MACRO_IDS: frozenset[int] = frozenset(
    {
        # 스포츠
        1,        # Sports
        100350,   # Soccer
        102232,   # FIFA World Cup
        102350,   # 2026 FIFA World Cup
        105315,   # Tournament Futures
        100219,   # Golf
        102112,   # PGA TOUR
        102446,   # The Masters
        104278,   # invitational
        104279,   # augusta
        # 엔터테인먼트
        53,       # Movies
        18,       # Awards
        596,      # Culture (pop-culture)
        102109,   # GTA VI
        # 개인/사건
        756,      # Epstein
        102424,   # Maxwell
        102429,   # Ghislaine Maxwell
        105562,   # Graham Platner
        105151,   # James Talarico
        105150,   # Ken Paxton
        1104,     # bernie sanders
    }
)


# 경제/크립토/지정학/정치 등 매크로 관련. 넓게 (애매하면 포함).
MACRO_IDS: frozenset[int] = frozenset(
    {
        # 경제/금융
        120,      # Finance
        100328,   # Economy
        101800,   # Economic Policy
        159,      # Fed
        100196,   # Fed Rates
        101550,   # Jerome Powell
        105160,   # Fiscal
        100207,   # Taxes
        102599,   # IPO
        600,      # IPOs
        102859,   # Token Sales
        1312,     # Crypto Prices
        105297,   # Crypto Listings
        105292,   # Crypto Legal
        # 크립토
        21,       # Crypto
        235,      # Bitcoin
        102785,   # Metamask
        102784,   # Consensys
        136,      # Airdrops
        336,      # token launch
        # 지정학
        100265,   # Geopolitics
        101253,   # Macro Geopolitics
        101794,   # Foreign Policy
        366,      # world affairs
        103027,   # Ukraine Peace Deal
        96,       # Ukraine
        303,      # China
        95,       # Russia
        180,      # Israel
        78,       # Iran
        192,      # NATO
        154,      # Middle East
        166,      # South Korea
        101270,   # Turkey
        # 기술/AI
        439,      # AI
        835,      # artificial intelligence
        662,      # llm
        1401,     # Tech
        101999,   # Big Tech
        537,      # OpenAI
        # 정치 (넓게 포함, 블랙리스트 우선 로직이 오염 필터)
        2,        # Politics
        144,      # Elections
        1101,     # US Election
        1597,     # Global Elections
        101206,   # World Elections
        126,      # Trump
        101191,   # Trump Presidency
        102886,   # President
        514,      # Congress
        100199,   # Senate
        264,      # Primaries
        102670,   # California Governor
    }
)


def classify(tag_ids: set[int]) -> Classification | None:
    """태그 ID 집합으로 마켓 분류.

    블랙리스트 우선: NON_MACRO_IDS 히트 시 즉시 NON_MACRO.
    이후 화이트리스트: MACRO_IDS 히트 시 MACRO.
    둘 다 없으면 None (UNKNOWN → 저장 안 함).

    Args:
        tag_ids: 마켓의 태그 ID 집합.

    Returns:
        Classification 값 또는 None.
    """
    if tag_ids & NON_MACRO_IDS:
        return Classification.NON_MACRO
    if tag_ids & MACRO_IDS:
        return Classification.MACRO
    return None
