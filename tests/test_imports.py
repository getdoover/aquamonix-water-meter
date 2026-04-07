"""
Basic tests for the application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from aquamonix_water_meter.application import AquamonixWaterMeterApplication

    assert AquamonixWaterMeterApplication


def test_config():
    from aquamonix_water_meter.app_config import AquamonixWaterMeterConfig

    config = AquamonixWaterMeterConfig()
    assert isinstance(config.to_schema(), dict)


def test_ui():
    from aquamonix_water_meter.app_ui import AquamonixWaterMeterUI

    assert AquamonixWaterMeterUI


def test_tags():
    from aquamonix_water_meter.app_tags import AquamonixWaterMeterTags

    assert AquamonixWaterMeterTags


def test_state():
    from aquamonix_water_meter.app_state import AquamonixWaterMeterState

    assert AquamonixWaterMeterState


def test_record():
    from aquamonix_water_meter.record import Record

    values = [0] * 42
    record = Record(values)
    assert record.total is not None
    assert record.current_flow is not None
    assert record.battery_volts is not None
    assert record.solar_volts is not None
