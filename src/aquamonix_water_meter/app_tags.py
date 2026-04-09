from pydoover.tags import Tag, Tags


class AquamonixWaterMeterTags(Tags):
    # Display values (updated each loop from modbus readings)
    last_flow = Tag("number", default=None)
    last_event_counter = Tag("number", default=None)
    last_total = Tag("number", default=None)
    last_batt_volts = Tag("number", default=None)
    last_solar_volts = Tag("number", default=None)
    comms_active = Tag("boolean", default=False)
    time_last_update = Tag("number", default=None)

    # Persisted state
    last_time_non_zero_flow = Tag("number", default=0)
    last_event_counter_zero = Tag("number", default=0)

    # User-set thresholds (set via UI handlers)
    shutdown_threshold = Tag("number", default=None)

    # Cross-app tags for pump control
    alert_triggered = Tag("boolean", default=False)
    alert_message_short = Tag("string", default=None)
    alert_message_long = Tag("string", default=None)

    app_display_name = Tag("string", default="Aquamonix Water Meter")
