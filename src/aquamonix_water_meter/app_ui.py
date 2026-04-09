from pydoover import ui

from .app_config import AquamonixWaterMeterConfig
from .app_tags import AquamonixWaterMeterTags


class AquamonixWaterMeterUI(
    ui.UI, display_name=AquamonixWaterMeterTags.app_display_name
):
    config: AquamonixWaterMeterConfig

    tabs = ui.TabContainer(
        display_name="Tabs",
        children=[
            ui.Container(
                "Meter",
                children=[
                    ui.NumericVariable(
                        "Flow",
                        units="ML/day",
                        value=AquamonixWaterMeterTags.last_flow,
                        form=ui.Widget.radial,
                    ),
                    ui.NumericVariable(
                        "Meter Total",
                        units="ML",
                        value=AquamonixWaterMeterTags.last_total,
                    ),
                    ui.Timestamp(
                        "Last Read",
                        value=AquamonixWaterMeterTags.time_last_update,
                    ),
                    ui.Button("Get Now"),
                ],
            ),
            ui.Container(
                "Event",
                children=[
                    ui.NumericVariable(
                        "This Event",
                        units="ML",
                        value=AquamonixWaterMeterTags.last_event_counter,
                    ),
                    ui.FloatInput(
                        "Send Alert At",
                        name="alert_counter",
                        units="ML",
                        min_val=0,
                        help_str="Send a notification when event total reaches this value (ML)",
                        default=None,
                    ),
                    ui.FloatInput(
                        "Shutdown Pump At",
                        name="shutdown_counter",
                        units="ML",
                        min_val=0,
                        help_str="Stop pumping when event total reaches this value (ML)",
                        default=None,
                    ),
                    ui.Button("Reset Event", requires_confirm=True),
                ],
            ),
        ]
    )

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
        ],
        is_collapsed=True,
    )

    async def setup(self):
        max_flow = self.config.max_flow.value
        print(dir(self.tabs.meter))

        for elem in (self.tabs.meter.flow, self.tabs.meter.meter_total, self.tabs.event.this_event):
            elem.precision = 1 if max_flow >= 100 else 2

        self.tabs.meter.flow.ranges = [
            ui.Range(None, 0, max_flow * 0.15, ui.Colour.blue),
            ui.Range(None, max_flow * 0.15, max_flow, ui.Colour.green),
        ]

        self.tabs.event.shutdown_counter.hidden = not self.config.allow_shutdown.value

def export():
    # from pathlib import Path
    # AquamonixWaterMeterUI.export(
    #     Path(__file__).parents[2] / "doover_config.json",
    #     "aquamonix_water_meter",
    # )
    pass
