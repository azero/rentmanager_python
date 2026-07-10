import os

import pytest

from rentmanager_api import RentManagerClient


def _live_env_present() -> bool:
    return all(os.getenv(name) for name in ("RM_CORP_ID", "RM_USERNAME", "RM_PASSWORD"))


@pytest.mark.skipif(not _live_env_present(), reason="Rent Manager live credentials are not configured.")
def test_live_read_smoke_lists_one_user_or_tenant():
    location_raw = os.getenv("RM_LOCATION_ID")
    client = RentManagerClient(
        corp_id=os.environ["RM_CORP_ID"],
        username=os.environ["RM_USERNAME"],
        password=os.environ["RM_PASSWORD"],
        location_id=int(location_raw) if location_raw else None,
        max_retries=1,
    )

    try:
        users = client.users.list(page_size=1)
        assert isinstance(users, list)
    finally:
        client.close()


@pytest.mark.skipif(not _live_env_present(), reason="Rent Manager live credentials are not configured.")
@pytest.mark.skipif(
    os.getenv("RM_LIVE_WRITE_TESTS") not in {"1", "true", "TRUE", "yes", "YES"},
    reason="Set RM_LIVE_WRITE_TESTS=1 to allow live write/action tests.",
)
def test_live_write_tests_are_explicitly_gated():
    assert os.getenv("RM_LIVE_WRITE_TESTS")
