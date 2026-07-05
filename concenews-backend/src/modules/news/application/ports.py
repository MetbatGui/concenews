"""News 모듈 application 계층 ports (인터페이스).

Hexagonal architecture 원칙:
- Port (인터페이스) 는 안쪽 (application) 이 정의.
- Adapter (구현) 는 바깥쪽 (infrastructure) 이 구현.
- Dependency Inversion: infrastructure → application.
"""
from typing import Protocol
from uuid import UUID


class IdGenerator(Protocol):
    """Identity 발급 port.

    구현체는 매 호출마다 unique identity 반환.
    """

    def generate(self) -> UUID:
        """다음 identity 반환."""
        ...
