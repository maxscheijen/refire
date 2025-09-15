import time

import pytest
from typing_extensions import NoReturn

from refire import refire


def test_success_no_retry() -> None:
    calls = []

    @refire(tries=3)
    def func() -> str:
        calls.append(1)
        return "ok"

    assert func() == "ok"
    assert len(calls) == 1


def test_retry_on_exception() -> None:
    calls = []

    @refire(tries=3, delay=0)
    def func() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("fail")
        return "ok"

    assert func() == "ok"
    assert len(calls) == 3


def test_raises_after_tries_exceeded() -> None:
    @refire(tries=2, delay=0)
    def func() -> NoReturn:
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        func()


def test_custom_exception_type() -> None:
    class CustomException(Exception):
        pass

    calls = []

    @refire(exceptions=CustomException, tries=2, delay=0)
    def func() -> NoReturn:
        calls.append(1)
        raise CustomException("fail")

    with pytest.raises(CustomException):
        func()

    assert len(calls) == 2


def test_no_retry_on_other_exception() -> None:
    class CustomException(Exception):
        pass

    @refire(exceptions=CustomException, tries=2, delay=0)
    def func() -> NoReturn:
        raise ValueError("fail")

    with pytest.raises(ValueError):
        func()


def test_delay_and_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))
    calls = []

    @refire(tries=3, delay=1, backoff=2)
    def func() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise Exception("fail")
        return "ok"

    func()
    assert sleep_calls == [1, 2]


def test_max_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))
    calls = []

    @refire(tries=3, delay=2, backoff=3, max_delay=5)
    def func() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise Exception("fail")
        return "ok"

    func()
    assert sleep_calls == [2, 5]


def test_jitter_int(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))
    monkeypatch.setattr("random.uniform", lambda a, b=None: 0.5)
    calls = []

    @refire(tries=2, delay=1, jitter=1)
    def func() -> NoReturn:
        calls.append(1)
        raise Exception("fail")

    with pytest.raises(Exception):
        func()

    assert sleep_calls == [1]


def test_jitter_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))
    monkeypatch.setattr("random.uniform", lambda a, b=None: 0.5)
    calls = []

    @refire(tries=2, delay=1, jitter=(1, 2))
    def func() -> NoReturn:
        calls.append(1)
        raise Exception("fail")

    with pytest.raises(Exception):
        func()
    assert sleep_calls == [1]


def test_jitter_tuple_len1(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))
    monkeypatch.setattr("random.uniform", lambda a, b=None: 0.5)
    calls = []

    @refire(tries=2, delay=1, jitter=(1, 1))
    def func() -> NoReturn:
        calls.append(1)
        raise Exception("fail")

    with pytest.raises(Exception):
        func()
    assert sleep_calls == [1]


def test_infinite_tries(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))
    max_calls = 5
    calls = []

    @refire(tries=-1, delay=0)
    def func() -> str:
        calls.append(1)
        if len(calls) < max_calls:
            raise Exception("fail")
        return "ok"

    assert func() == "ok"
    assert len(calls) == max_calls
