"""Fixtures for the tests."""

from collections.abc import Iterator

import pytest
import responses


@pytest.fixture()
def http_responses() -> Iterator[responses.RequestsMock]:
    """Create a fake http response."""
    with responses.RequestsMock() as resp_mock:
        yield resp_mock
