import threading
from engine.state import get_setting, insert_earning, insert_decision
from services.decision_engine import approve_decision
from strategies.registry import get_enabled_strategies

class SchedulerThread(threading.Thread):
    def __init__(self, interval_seconds: int = 300):
        super().__init__(daemon=True)
        self.interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._nudge = threading.Event()

    def nudge(self):
        self._nudge.set()

    def run(self):
        import time
        while not self._stop.is_set():
            self._cycle()
            self._nudge.wait(timeout=self.interval_seconds)
            self._nudge.clear()

    def _cycle(self):
        auto = get_setting("AUTO_APPROVE_ENABLED", "false").lower() == "true"
        try:
            cap = float(get_setting("AUTO_APPROVE_THRESHOLD", "1.0"))
        except Exception:
            cap = 1.0
        for strat in get_enabled_strategies():
            earnings, proposals = strat.scan()
            for e in earnings:
                insert_earning(e.source, e.amount, e.note)
            for p in proposals:
                insert_decision(p.strategy, p.action, p.payload, p.estimated_value, p.note)
                if auto and 0 <= p.estimated_value <= cap:
                    approve_decision(-1, payload_override=p.payload, strategy_name=p.strategy)

    def stop(self):
        self._stop.set()
