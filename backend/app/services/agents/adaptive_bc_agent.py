from dataclasses import dataclass


@dataclass
class FPSState:
    fps: float
    object_count: int


@dataclass(frozen=True)
class ActionConfig:
    mode: str
    batch_size: int


class ComputeAgent:

    def __init__(self):
        self._ema_count = None
        self.alpha = 0.3

    def _smooth(self, value: float) -> float:
        if self._ema_count is None:
            self._ema_count = value
        else:
            self._ema_count = (
                self.alpha * value +
                (1 - self.alpha) * self._ema_count
            )
        return self._ema_count

    def decide(self, state: FPSState) -> ActionConfig:

        count = self._smooth(state.object_count)

        # -------------------------
        # 🟡 WARMUP
        # -------------------------
        if self._ema_count is None:
            return ActionConfig(mode="WARMUP", batch_size=2)

        # -------------------------
        # ⚡ LATENCY-FIRST BATCH CONTROL
        # -------------------------
        # higher load → smaller batch to avoid queue buildup
        if count > 25:
            mode = "LOW_LATENCY_HIGH_LOAD"
            batch_size = 2

        elif count > 10:
            mode = "LOW_LATENCY_MED_LOAD"
            batch_size = 4

        else:
            mode = "LOW_LATENCY_LOW_LOAD"
            batch_size = 8

        # -------------------------
        # 🛑 HARD LATENCY SAFETY CAP
        # -------------------------
        batch_size = max(1, min(batch_size, 8))

        return ActionConfig(
            mode=mode,
            batch_size=1
        )

