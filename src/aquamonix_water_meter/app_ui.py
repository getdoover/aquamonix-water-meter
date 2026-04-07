from pydoover import ui

from .app_config import AquamonixWaterMeterConfig
from .app_tags import AquamonixWaterMeterTags


class AquamonixWaterMeterUI(ui.UI):
    config: AquamonixWaterMeterConfig

    flow = ui.NumericVariable(
        "Flow",
        units="ML/day",
        value=AquamonixWaterMeterTags.last_flow,
        form=ui.Widget.radial,
    )

    this_event = ui.NumericVariable(
        "This Event",
        units="ML",
        value=AquamonixWaterMeterTags.last_event_counter,
    )

    alert_counter = ui.FloatInput(
        "Alert Counter",
        min_val=0,
        help_str="Send a notification when event total reaches this value (ML)",
    )

    shutdown_counter = ui.FloatInput(
        "Shutdown Counter",
        min_val=0,
        help_str="Stop pumping when event total reaches this value (ML)",
    )

    reset_event = ui.Button("Reset Event", requires_confirm=True)

    meter_total = ui.NumericVariable(
        "Meter Total (ML)",
        value=AquamonixWaterMeterTags.last_total,
    )

    last_read = ui.Timestamp(
        "Last Read",
        value=AquamonixWaterMeterTags.time_last_update,
    )

    get_now = ui.Button("Get Now")

    maintenance = ui.Submodule(
        "Maintenance",
        children=[
            ui.NumericVariable(
                "Battery",
                units="V",
                value=AquamonixWaterMeterTags.last_batt_volts,
                precision=1,
                ranges=[
                    ui.Range("Low", 11.5, 12.3, ui.Colour.yellow),
                    ui.Range("Good", 12.3, 13.0, ui.Colour.blue),
                    ui.Range("Charging", 13.0, 14.0, ui.Colour.green),
                    ui.Range("OverCharging", 14.0, 14.5, ui.Colour.red),
                ],
            ),
            ui.NumericVariable(
                "Solar",
                units="V",
                value=AquamonixWaterMeterTags.last_solar_volts,
                precision=1,
                ranges=[
                    ui.Range("Low", 0, 14.0, ui.Colour.blue),
                    ui.Range("Charging", 14.0, 25, ui.Colour.green),
                ],
            ),
            ui.BooleanVariable(
                "Comms Active",
                value=AquamonixWaterMeterTags.comms_active,
            ),
            ui.DatetimeInput("Last Battery Changed"),
            ui.DatetimeInput("New Battery Due"),
            ui.TextInput("Service Notes", is_text_area=True),
        ],
        is_collapsed=True,
    )

    async def setup(self):
        max_flow = self.config.max_flow.value

        for elem in (self.flow, self.this_event, self.meter_total):
            elem.precision = 1 if max_flow >= 100 else 2

        self.flow.ranges = [
            ui.Range(None, 0, max_flow * 0.15, ui.Colour.blue),
            ui.Range(None, max_flow * 0.15, max_flow, ui.Colour.green),
        ]

        self.shutdown_counter.hidden = not self.config.allow_shutdown.value
