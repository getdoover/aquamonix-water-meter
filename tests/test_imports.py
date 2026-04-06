"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from aquamonix_flow_meter.application import AquamonixFlowMeterApplication
    assert AquamonixFlowMeterApplication

def test_config():
    from aquamonix_flow_meter.app_config import AquamonixFlowMeterConfig

    config = AquamonixFlowMeterConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from aquamonix_flow_meter.app_ui import AquamonixFlowMeterUI
    assert AquamonixFlowMeterUI

def test_state():
    from aquamonix_flow_meter.app_state import AquamonixFlowMeterState
    assert AquamonixFlowMeterState