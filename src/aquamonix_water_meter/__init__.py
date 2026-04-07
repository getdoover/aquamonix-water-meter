from pydoover.docker import run_app

from .application import AquamonixWaterMeterApplication


def main():
    """
    Run the Aquamonix Flow Meter application.
    """
    run_app(AquamonixWaterMeterApplication())
