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
    motor_control_app = config.ApplicationInstall(
        "Pump Control App",
        name="motor_control_app",
        default="",
        description="The motor control install on this device to send a 'stop' "
        "RPC to when the shutdown target is reached, e.g. "
        "'motor_control_3_wire_1'. Leaving it empty sends the stop to every app "
        "on the device that handles one. Only used when Allow Shutdown is on.",
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
