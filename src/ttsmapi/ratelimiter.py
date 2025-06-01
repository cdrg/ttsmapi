"""
Naïve, bare-bones rate limiter to control the rate of requests, such as to an API.

Uses Generic Cell Rate Algorithm (GCRA).

Credit: https://smarketshq.com/implementing-gcra-in-python-5df1f11aaa96
"""

from typing import Dict
import shelve
from datetime import datetime, timedelta, timezone

class RateLimit:
    """
    Represents a rate limit as a count within a period.

    Limitation: Uses only seconds as a unit of time.
    """
    def __init__(self, count: int, period: timedelta) -> None:
        """Initialize a RateLimit object.
        Args:
            count (int): The number of requests allowed in the period.
            period (timedelta): The time period over which the requests are counted.
        Raises:
            ValueError: If count is not at least 1, or if period is not at least 1 second.
            TypeError: If period is not a timedelta object.
        """
        if count <= 0:
            raise ValueError("Count must be at least 1")
        if not isinstance(period, timedelta):
            raise TypeError("Period must be a timedelta object")
        if period.total_seconds() <= 0:
            raise ValueError("Period must be at least 1 second")

        self.count: int = count
        self.period: timedelta = period

    @property
    def inverse(self) -> float:
        """Returns the inverse of the rate limit, eg the period divided by the count, in seconds.
        Returns:
            float: The inverse of the rate limit in seconds.
        """
        return self.period.total_seconds() / self.count

class Store:
    """
    A store of theoretical arrival times to track RateLimits.

    Memory-only unless `persist` is True, in which case it's persisted to a shelve file.

    Limitation: Uses only seconds as a unit of time.
    """
    def __init__(self, persist: bool=False) -> None:
        """Initialize a Store object, optionally persisting to a shelve file.
        Args:
            persist (bool): If True, the store will persist to a shelve file.
        Raises:
        """
        if persist:
            self.dict: shelve.Shelf|Dict = shelve.open('.ratelimiter_store')
        else:
            self.dict: shelve.Shelf|Dict = {}

    def __del__(self) -> None:
        if isinstance(self.dict, shelve.Shelf):
            self.dict.close()

    def get_tatime(self, key: str) -> datetime:
        """Get the theoretical arrival time for a key in the store, or the current time if not in the store.
        Args:
            key (str): The key to retrieve the theoretical arrival time for.
        Returns:
            datetime: The theoretical arrival time for the key, or the current time if not found.
        """
        if key in self.dict:
            return self.dict[key]
        return datetime.now(timezone.utc)

    def set_tatime(self, key: str, tatime: datetime) -> None:
        """Set the theoretical arrival time for a key in the store.
        Args:
            key (str): The key to set the theoretical arrival time for.
            tatime (datetime): The theoretical arrival time to set.
        """
        self.dict[key] = tatime

    def update(self, key: str, ratelimit: RateLimit) -> bool:
        """Update the theoretical arrival time for a key based on a rate limit.
        Args:
            key (str): The key to update the theoretical arrival time for.
            ratelimit (RateLimit): The rate limit to apply.
        Returns:
            bool: True if the request should be rejected, False otherwise.
        """
        now = datetime.now(timezone.utc)
        tatime = max(self.get_tatime(key), now)
        separation = (tatime - now).total_seconds()
        max_interval = ratelimit.period.total_seconds() - ratelimit.inverse
        if separation > max_interval:
            reject = True
        else:
            reject = False
            new_tatime = max(tatime, now) + timedelta(seconds=ratelimit.inverse)
            self.set_tatime(key, new_tatime)
        return reject
