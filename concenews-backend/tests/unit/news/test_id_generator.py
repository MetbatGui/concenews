"""IdGenerator (UUIDv7) unit tests."""
from uuid import UUID

from src.modules.news.application.ports import IdGenerator
from src.modules.news.infrastructure.id_generator import UuidV7Generator


class TestUuidV7Generator:
    """UUIDv7 발급기 검증."""

    def test_satisfies_id_generator_port(self):
        """UuidV7Generator 는 IdGenerator port 계약을 만족한다.

        Given: UuidV7Generator 인스턴스
        When: IdGenerator Protocol 로 typing 확인 (runtime_checkable 없이 구조적 검증)
        Then: generate() 메서드 존재, UUID 반환
        """
        gen: IdGenerator = UuidV7Generator()

        result = gen.generate()

        assert isinstance(result, UUID)

    def test_generate_returns_uuid_instance(self):
        """generate() 는 stdlib uuid.UUID 를 반환한다.

        Given: UuidV7Generator 인스턴스
        When: generate() 호출
        Then: uuid.UUID 인스턴스
        """
        gen = UuidV7Generator()

        result = gen.generate()

        assert isinstance(result, UUID)

    def test_generate_returns_version_7(self):
        """발급된 UUID 는 v7 (RFC 9562).

        Given: UuidV7Generator 인스턴스
        When: generate() 호출
        Then: uuid.version == 7
        """
        gen = UuidV7Generator()

        result = gen.generate()

        assert result.version == 7

    def test_generate_returns_unique_values(self):
        """연속 호출은 서로 다른 UUID 를 반환한다.

        Given: UuidV7Generator 인스턴스
        When: generate() 2회 호출
        Then: 두 값이 서로 다름
        """
        gen = UuidV7Generator()

        first = gen.generate()
        second = gen.generate()

        assert first != second

    def test_generate_returns_time_ordered_values(self):
        """v7 는 시간순 정렬 가능 (앞선 호출 < 나중 호출).

        Given: UuidV7Generator 인스턴스
        When: generate() 2회 순차 호출
        Then: 첫 UUID < 두 번째 UUID (bytes 비교)
        """
        gen = UuidV7Generator()

        first = gen.generate()
        second = gen.generate()

        assert first.bytes < second.bytes
