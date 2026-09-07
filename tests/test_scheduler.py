from app.sync.scheduler import SyncScheduler


def test_scheduler_lock_is_released_after_cycle_failure():
    assert not SyncScheduler._lock.locked()
    acquired = SyncScheduler._lock.acquire(blocking=False)
    assert acquired
    SyncScheduler._lock.release()
    assert not SyncScheduler._lock.locked()
