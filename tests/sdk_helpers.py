"""Shared helpers simulating Cosmos SDK math / store primitives."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable

# ---------------------------------------------------------------------------
# sdkmath emulation
# ---------------------------------------------------------------------------

MAX_INT64 = (1 << 63) - 1  # 9_223_372_036_854_775_807
MAX_UINT64 = (1 << 64) - 1  # 18_446_744_073_709_551_615


class Int:
    """Minimal stand-in for sdkmath.Int (arbitrary-precision integer)."""

    def __init__(self, value: int = 0):
        self._v = int(value)

    def add(self, other: "Int") -> "Int":
        return Int(self._v + other._v)

    def sub(self, other: "Int") -> "Int":
        return Int(self._v - other._v)

    def mul(self, other: "Int") -> "Int":
        return Int(self._v * other._v)

    def int64(self) -> int:
        if self._v > MAX_INT64 or self._v < -(MAX_INT64 + 1):
            raise OverflowError(
                f"Int64() out of bound: {self._v} > MaxInt64 ({MAX_INT64})"
            )
        return self._v

    def is_zero(self) -> bool:
        return self._v == 0

    def gt(self, other: "Int") -> bool:
        return self._v > other._v

    def gte(self, other: "Int") -> bool:
        return self._v >= other._v

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Int):
            return self._v == other._v
        return NotImplemented

    def __repr__(self) -> str:
        return f"Int({self._v})"


class Dec:
    """Minimal stand-in for sdk.Dec (fixed-point decimal)."""

    def __init__(self, value: str | int | Decimal = "0"):
        self._v = Decimal(str(value))

    def mul(self, other: "Dec") -> "Dec":
        return Dec(self._v * other._v)

    def quo(self, other: "Dec") -> "Dec":
        return Dec(self._v / other._v)

    def truncate_int(self) -> Int:
        return Int(int(self._v))

    def is_zero(self) -> bool:
        return self._v == 0

    def gt(self, other: "Dec") -> bool:
        return self._v > other._v

    def gte(self, other: "Dec") -> bool:
        return self._v >= other._v

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Dec):
            return self._v == other._v
        return NotImplemented

    def __repr__(self) -> str:
        return f"Dec({self._v})"


# ---------------------------------------------------------------------------
# KV-store emulation
# ---------------------------------------------------------------------------


class KVStore:
    """Minimal ordered key-value store emulating IAVL behaviour."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def set(self, key: str, value: bytes) -> None:
        self._data[key] = value

    def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def has(self, key: str) -> bool:
        return key in self._data

    def iterate_prefix(self, prefix: str) -> list[tuple[str, bytes]]:
        return sorted(
            (k, v) for k, v in self._data.items() if k.startswith(prefix)
        )

    def keys(self) -> list[str]:
        return sorted(self._data.keys())


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class Region:
    region_id: str = ""
    treasure_addr: str = ""
    delegate_interest: Dec = field(default_factory=lambda: Dec("0"))
    fixed_deposit_amount: Int = field(default_factory=lambda: Int(0))
    region_share: Dec = field(default_factory=lambda: Dec("0"))
    admin: str = ""
