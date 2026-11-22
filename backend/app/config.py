import math
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_workers: int = 5
    timeout: float = 15.0
    verify_ssl: bool = True
    max_spec_size: int = 5 * 1024 * 1024

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            max_workers = int(os.getenv("MAX_WORKERS", "5"))
            timeout = float(os.getenv("REQUEST_TIMEOUT", "15"))
            max_spec_size = int(os.getenv("MAX_SPEC_SIZE", str(5 * 1024 * 1024)))
        except ValueError as error:
            raise ValueError(
                "MAX_WORKERS, REQUEST_TIMEOUT and MAX_SPEC_SIZE "
                "must contain valid numeric values."
            ) from error

        verify_ssl_value = os.getenv("VERIFY_SSL", "true").lower()

        if verify_ssl_value not in {"true", "1", "yes", "false", "0", "no"}:
            raise ValueError("VERIFY_SSL must be true, false, 1, 0, yes or no.")

        if not 1 <= max_workers <= 32:
            raise ValueError("MAX_WORKERS must be between 1 and 32.")

        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT must be a positive number.")

        if max_spec_size <= 0:
            raise ValueError("MAX_SPEC_SIZE must be a positive integer.")

        return cls(
            max_workers=max_workers,
            timeout=timeout,
            verify_ssl=verify_ssl_value in {"true", "1", "yes"},
            max_spec_size=max_spec_size,
        )


settings = Settings.from_env()
