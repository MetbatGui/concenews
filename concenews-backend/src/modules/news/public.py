"""News 모듈의 공개 인터페이스.

다른 모듈은 이 파일에서만 import 가능.
구현 세부사항 (domain, application, presentation 내부)은 외부 노출 금지.
"""

from .presentation.schemas import GetNewsResponse, NewsItemResponse

__all__ = ["GetNewsResponse", "NewsItemResponse"]
