import logging
import time

from pydoover.state import StateMachine


DEFAULT_SLEEP_TIME = 60 * 10.5  # 10.5 minutes
DEFAULT_AWAKE_TIME = 60 * 1.5  # 1.5 minutes
DEFAULT_WAKE_DELAY = 30  # 30 seconds

# Waking early for an event target: read this long after the projected
# crossing, never after less than this much sleep, and never on a meter
# battery at or below this voltage.
EARLY_WAKE_MARGIN = 60
MIN_SLEEP_TIME = 60
MIN_EARLY_WAKE_VOLTS = 12.0


log = logging.getLogger(__name__)


def get_sleep_time(voltage: float) -> float:
    if voltage is None or voltage > 12.9:
        return DEFAULT_SLEEP_TIME

    if 12.5 < voltage <= 12.9:
        return DEFAULT_SLEEP_TIME * 1.5
    if 12.2 < voltage <= 12.5:
        return DEFAULT_SLEEP_TIME * 3

    # voltage <= 12.2
    return DEFAULT_SLEEP_TIME * 5


class AquamonixWaterMeterState:
    state: str

    states = [
        {"name": "initial"},
        {"name": "sleeping", "timeout": DEFAULT_SLEEP_TIME, "on_timeout": "awaken"},
        {
            "name": "awake_init",
            "timeout": DEFAULT_WAKE_DELAY,
            "on_timeout": "initialised",
        },
        {"name": "awake_rt", "timeout": DEFAULT_AWAKE_TIME, "on_timeout": "goto_sleep"},
    ]

    transitions = [
        {"trigger": "initialise", "source": "initial", "dest": "awake_init"},
        {"trigger": "awaken", "source": "sleeping", "dest": "awake_init"},
        {"trigger": "initialised", "source": "awake_init", "dest": "awake_rt"},
        {"trigger": "goto_sleep", "source": "awake_init", "dest": "sleeping"},
        {"trigger": "goto_sleep", "source": "awake_rt", "dest": "sleeping"},
    ]

    def __init__(self):
        self.state_machine = StateMachine(
            states=self.states,
            transitions=self.transitions,
            model=self,
            initial="initial",
            queued=True,
        )

        self.should_request = False
        self.slept_at: float = 0

    async def spin(self, battery_voltage: float, wake_at: float | None = None):
        """Advance the state machine.

        ``wake_at`` is when the event is projected to reach its next target, in
        epoch seconds. The sleep timeout is only read on entering the sleeping
        state, so waking early for a target has to happen here instead.
        """
        self.state_machine.get_state("sleeping").timeout = get_sleep_time(
            battery_voltage
        )

        if self.state == "initial":
            await self.initialise()
        elif self.state == "sleeping" and self._should_wake_early(
            battery_voltage, wake_at
        ):
            log.info("Waking early to read the meter as it reaches an event target")
            await self.awaken()

    def _should_wake_early(self, battery_voltage, wake_at) -> bool:
        if wake_at is None or battery_voltage is None:
            return False
        if battery_voltage <= MIN_EARLY_WAKE_VOLTS:
            return False

        now = time.time()
        return now - self.slept_at >= MIN_SLEEP_TIME and now >= wake_at + EARLY_WAKE_MARGIN

    async def on_enter_sleeping(self):
        self.should_request = False
        self.slept_at = time.time()

    async def on_enter_awake_init(self):
        self.should_request = True

    async def on_enter_awake_rt(self):
        self.should_request = True
