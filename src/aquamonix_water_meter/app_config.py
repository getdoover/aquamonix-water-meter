from pathlib import Path

from pydoover import config
from pydoover.config import ApplicationPosition
from pydoover.docker.modbus import ModbusConfig


class AquamonixWaterMeterConfig(config.Schema):
    modbus_id = config.Integer(
        "Modbus ID", description="Modbus ID for the meter"
    )
    max_flow = config.Integer(
        "Max Flow",
        description="Max flow value for the meter",
        exclusive_minimum=0,
    )
    allow_shutdown = config.Boolean(
        "Allow Shutdown",
        description="Allow shutdown of the pump",
        default=True,
    )
    stay_online_seconds = config.Integer(
        "Stay Online Seconds",
        description="Time to stay online in seconds",
        default=120,
        hidden=True,
    )
    shutdown_sleep_seconds = config.Integer(
        "Shutdown Time",
        description="Time to stay shutdown in seconds",
        default=900,
        hidden=True,
    )
    position = ApplicationPosition()
    modbus_config = ModbusConfig()


def export():
    AquamonixWaterMeterConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "aquamonix_water_meter",
    )
