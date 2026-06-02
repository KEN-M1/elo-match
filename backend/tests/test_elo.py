import unittest

from app.rating import calculate_elo


class EloTests(unittest.TestCase):
    def test_equal_ratings_move_by_sixteen_points(self) -> None:
        result = calculate_elo(1000, 1000)

        self.assertEqual(result.winner_rating_after, 1016)
        self.assertEqual(result.loser_rating_after, 984)
        self.assertEqual(result.winner_delta, 16)
        self.assertEqual(result.loser_delta, -16)

    def test_heavy_favorite_gains_small_delta(self) -> None:
        result = calculate_elo(1400, 1000)

        self.assertLess(result.winner_delta, 4)
        self.assertGreater(result.loser_delta, -4)

    def test_heavy_underdog_gains_large_delta(self) -> None:
        result = calculate_elo(1000, 1400)

        self.assertGreater(result.winner_delta, 28)
        self.assertLess(result.loser_delta, -28)

    def test_k_factor_controls_delta_size(self) -> None:
        low_k = calculate_elo(1000, 1000, k_factor=16)
        high_k = calculate_elo(1000, 1000, k_factor=64)

        self.assertEqual(low_k.winner_delta, 8)
        self.assertEqual(high_k.winner_delta, 32)

    def test_rating_floor_prevents_loser_from_falling_below_floor(self) -> None:
        result = calculate_elo(101, 101, rating_floor=100)

        self.assertEqual(result.loser_rating_after, 100)
        self.assertEqual(result.loser_delta, -1)

    def test_symmetric_equal_match_deltas_cancel(self) -> None:
        result = calculate_elo(1000, 1000)

        self.assertEqual(result.winner_delta + result.loser_delta, 0)


if __name__ == "__main__":
    unittest.main()
