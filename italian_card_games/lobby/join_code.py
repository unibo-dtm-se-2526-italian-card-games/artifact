from dataclasses import dataclass
from random import Random

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LENGTH = 6


@dataclass(frozen=True, slots=True)
class JoinCode:
    """FR-27: the short code a creator shares so others can join a lobby.

    It is trimmed and upper-cased on creation. The alphabet leaves out the
    look-alikes 0, 1, O and I, so a code read aloud or copied by hand is not misread.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if len(normalized) != LENGTH:
            raise ValueError(f"a join code has exactly {LENGTH} characters")
        if not set(normalized) <= set(ALPHABET):
            raise ValueError("a join code has invalid characters")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def random(cls, rng: Random) -> "JoinCode":
        """A fresh code drawn from the injected generator."""
        return cls("".join(rng.choice(ALPHABET) for _ in range(LENGTH)))

    def __str__(self) -> str:
        return self.value
