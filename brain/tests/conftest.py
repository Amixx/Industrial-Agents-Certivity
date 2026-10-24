import pytest

# Fixtures that build the obligation base from the whole corpus.
SLOW_FIXTURES = {"kb", "built"}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if SLOW_FIXTURES & set(getattr(item, "fixturenames", ())) or "two_builds" in item.name:
            item.add_marker(pytest.mark.slow)
