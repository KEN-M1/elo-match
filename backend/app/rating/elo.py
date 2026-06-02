from dataclasses import dataclass


@dataclass(frozen=True)
class EloResult:
    winner_rating_before: float
    loser_rating_before: float
    winner_rating_after: float
    loser_rating_after: float
    winner_delta: float
    loser_delta: float


def calculate_elo(
    winner_rating: float,
    loser_rating: float,
    k_factor: int = 32,
    rating_floor: float = 100.0,
) -> EloResult:
    """Calculate a confirmed 1v1 Elo result."""

    expected = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    raw_delta = round(k_factor * (1 - expected), 2)
    winner_after = round(winner_rating + raw_delta, 2)
    loser_after = round(max(rating_floor, loser_rating - raw_delta), 2)

    return EloResult(
        winner_rating_before=winner_rating,
        loser_rating_before=loser_rating,
        winner_rating_after=winner_after,
        loser_rating_after=loser_after,
        winner_delta=round(winner_after - winner_rating, 2),
        loser_delta=round(loser_after - loser_rating, 2),
    )
