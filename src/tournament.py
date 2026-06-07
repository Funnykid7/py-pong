from dataclasses import dataclass, field


@dataclass
class Slot:
    label: str
    is_cpu: bool
    difficulty: str  # EASY/MEDIUM/HARD/INSANE — ignored when is_cpu is False


@dataclass
class Match:
    slot_a: int        # index into TournamentManager.slots
    slot_b: int
    winner: int | None = None  # slot index of winner; None = not yet played


class TournamentManager:
    def __init__(self, slots: list[Slot]):
        assert len(slots) in (4, 8), f"Tournament requires 4 or 8 slots, got {len(slots)}"
        self.size: int = len(slots)
        self.slots: list[Slot] = slots
        self.rounds: list[list[Match]] = self._build_rounds()
        self.round_idx: int = 0
        self.match_idx: int = 0

    def _build_rounds(self) -> list[list[Match]]:
        first = [Match(i * 2, i * 2 + 1) for i in range(self.size // 2)]
        rounds: list[list[Match]] = [first]
        n_more = {4: 1, 8: 2}[self.size]
        for _ in range(n_more):
            prev_len = len(rounds[-1])
            rounds.append([Match(-1, -1) for _ in range(prev_len // 2)])
        return rounds

    def next_match(self) -> Match | None:
        if self.is_complete():
            return None
        return self.rounds[self.round_idx][self.match_idx]

    def record_result(self, winner_slot_idx: int) -> None:
        match = self.rounds[self.round_idx][self.match_idx]
        match.winner = winner_slot_idx
        # Propagate to next round
        next_round_idx = self.round_idx + 1
        if next_round_idx < len(self.rounds):
            next_match_pos = self.match_idx // 2
            next_match = self.rounds[next_round_idx][next_match_pos]
            if self.match_idx % 2 == 0:
                next_match.slot_a = winner_slot_idx
            else:
                next_match.slot_b = winner_slot_idx
        # Advance pointer
        self.match_idx += 1
        if self.match_idx >= len(self.rounds[self.round_idx]):
            self.round_idx += 1
            self.match_idx = 0

    def is_complete(self) -> bool:
        return all(m.winner is not None for m in self.rounds[-1])

    def champion(self) -> Slot | None:
        if not self.is_complete():
            return None
        return self.slots[self.rounds[-1][0].winner]
