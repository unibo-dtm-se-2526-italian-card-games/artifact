import re
from dataclasses import dataclass

MIN_LENGTH = 3
MAX_LENGTH = 20
_ALLOWED = re.compile(r"[A-Za-z0-9_-]+")


@dataclass(frozen=True, slots=True, eq=False)
class Nickname:
    """FR-26: the name a human registers, unique regardless of letter case.

    `value` keeps the casing the player chose, for display. Two nicknames are
    equal when their `key` is, so "Davide" and "davide" are the same name.
    """

    value: str

    def __post_init__(self) -> None:
        trimmed = self.value.strip()
        if len(trimmed) < MIN_LENGTH:
            raise ValueError(f"a nickname needs at least {MIN_LENGTH} characters")
        if len(trimmed) > MAX_LENGTH:
            raise ValueError(f"a nickname has at most {MAX_LENGTH} characters")
        if not _ALLOWED.fullmatch(trimmed):
            raise ValueError("a nickname can only contain letters, digits, '_' and '-'")
        object.__setattr__(self, "value", trimmed)

    @property
    def key(self) -> str:
        """The case-insensitive form used to decide whether a name is taken."""
        return self.value.lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Nickname):
            return NotImplemented
        return self.key == other.key

    def __hash__(self) -> int:
        return hash(self.key)

    def __str__(self) -> str:
        return self.value
