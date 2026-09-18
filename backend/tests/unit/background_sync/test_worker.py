import asyncio

import pytest
from arq import Retry

from veya.application.instagram.sync_service import InstagramSyncError
from veya.infrastructure.jobs import worker


class FakeRedis:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple, dict]] = []

    async def enqueue_job(self, name, *args, **kwargs):
        self.jobs.append((name, args, kwargs))
        return object()


def test_scheduler_enqueues_claimed_jobs(monkeypatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(worker, "_prepare_due_jobs", lambda: [(11, 4), (12, 5)])

    count = asyncio.run(worker.enqueue_due_instagram_accounts({"redis": redis}))

    assert count == 2
    assert [job[0] for job in redis.jobs] == [
        "sync_instagram_account",
        "sync_instagram_account",
    ]
    assert redis.jobs[0][1] == (11,)
    assert redis.jobs[0][2]["_job_id"] == "veya-instagram-sync-11"


def test_worker_marks_retrying_before_arq_retry(monkeypatch) -> None:
    marked: list[tuple[int, int, str]] = []

    def fail(job_id: int, attempt_count: int):
        raise RuntimeError("temporary failure")

    monkeypatch.setattr(worker, "_run_sync_job", fail)
    monkeypatch.setattr(
        worker,
        "_mark_retrying",
        lambda job_id, attempt_count, error: marked.append(
            (job_id, attempt_count, error)
        ),
    )

    with pytest.raises(Retry):
        asyncio.run(
            worker.sync_instagram_account(
                {"job_try": 1},
                99,
            )
        )

    assert marked == [(99, 1, "temporary failure")]


def test_worker_marks_failed_after_last_attempt(monkeypatch) -> None:
    failed: list[tuple[int, int, str]] = []

    def fail(job_id: int, attempt_count: int):
        raise RuntimeError("permanent failure")

    monkeypatch.setattr(worker, "_run_sync_job", fail)
    monkeypatch.setattr(
        worker,
        "_mark_failed",
        lambda job_id, attempt_count, error: failed.append(
            (job_id, attempt_count, error)
        ),
    )

    with pytest.raises(RuntimeError, match="permanent failure"):
        asyncio.run(
            worker.sync_instagram_account(
                {"job_try": 3},
                100,
            )
        )

    assert failed == [(100, 3, "permanent failure")]


def test_worker_does_not_retry_reconnect_required_error(monkeypatch) -> None:
    failed: list[tuple[int, int, str]] = []
    retrying: list[tuple[int, int, str]] = []

    def fail(job_id: int, attempt_count: int):
        raise InstagramSyncError(
            "Instagram access token has expired; reconnect the account",
            reconnect_required=True,
        )

    monkeypatch.setattr(worker, "_run_sync_job", fail)
    monkeypatch.setattr(
        worker,
        "_mark_failed",
        lambda job_id, attempt_count, error: failed.append(
            (job_id, attempt_count, error)
        ),
    )
    monkeypatch.setattr(
        worker,
        "_mark_retrying",
        lambda job_id, attempt_count, error: retrying.append(
            (job_id, attempt_count, error)
        ),
    )

    with pytest.raises(InstagramSyncError):
        asyncio.run(
            worker.sync_instagram_account(
                {"job_try": 1},
                101,
            )
        )

    assert len(failed) == 1
    assert failed[0][0:2] == (101, 1)
    assert retrying == []
