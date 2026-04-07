import logging

from pydoover.state import StateMachine


DEFAULT_SLEEP_TIME = 60 * 10.5  # 10.5 minutes
DEFAULT_AWAKE_TIME = 60 * 1.5  # 1.5 minutes
DEFAULT_WAKE_DELAY = 30  # 30 seconds


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

    async def spin(self, battery_voltage: float):
        self.state_machine.get_state("sleeping").timeout = get_sleep_time(
            battery_voltage
        )

        if self.state == "initial":
            await self.initialise()

    async def on_enter_sleeping(self):
        self.should_request = False

    async def on_enter_awake_init(self):
        self.should_request = True

    async def on_enter_awake_rt(self):
        self.should_request = True
