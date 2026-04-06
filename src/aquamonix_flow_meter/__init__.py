from pydoover.docker import run_app

from .application import AquamonixFlowMeterApplication
from .app_config import AquamonixFlowMeterConfig

def main():
    """
    Run the application.
    """
    run_app(AquamonixFlowMeterApplication(config=AquamonixFlowMeterConfig()))
