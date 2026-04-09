import logging
import time

from pydoover import ui
from pydoover.docker import Application

from .app_config import AquamonixWaterMeterConfig
from .app_tags import AquamonixWaterMeterTags
from .app_ui import AquamonixWaterMeterUI
from .app_state import AquamonixWaterMeterState
from .record import Record

log = logging.getLogger()

START_REG_NUM = 0
NUM_REGS = 42
REGISTER_TYPE = 4

ALERT_MESSAGE = "by water meter target"
ALERT_MESSAGE_LONG = "after the meter reached {}ML"


class AquamonixWaterMeterApplication(Application):
    config: AquamonixWaterMeterConfig
    tags: AquamonixWaterMeterTags

    config_cls = AquamonixWaterMeterConfig
    tags_cls = AquamonixWaterMeterTags
    ui_cls = AquamonixWaterMeterUI

    async def setup(self):
        self.state = AquamonixWaterMeterState()

        self.last_flow: float | None = None
        self.prev_non_null_flow = None
        self.last_non_null_flow = None

        self.last_loop_start: float = time.time()

        self.last_record: Record | None = None
        self.last_request_time: float = 0
        self.min_request_interval = 10

    async def main_loop(self):
        log.info(f"Last loop = {time.time() - self.last_loop_start} seconds")
        log.info(f"State: {self.state.state}")
        self.last_loop_start = time.time()

        # Update display name with current flow
        if self.last_flow is not None:
            if self.last_flow == 0:
                display_string = "0 ML/day"
            elif self.last_flow < 10:
                display_string = f"{round(self.last_flow, 1)} ML/day"
            else:
                display_string = f"{round(self.last_flow, 0)} ML/day"
        else:
            display_string = " - ML/day"

        await self.tags.app_display_name.set(f"{self.app_display_name}: {display_string}")

        # Update UI via tags
        await self._update_display_tags()

        # Spin state machine with battery voltage
        batt_volts = self.last_record and self.last_record.battery_volts
        await self.state.spin(batt_volts)
        if self.state.should_request:
            await self._send_request()

        # State-specific logic
        match self.state.state:
            case "sleeping":
                pass
            case "awake_init":
                self.last_flow = None
                if self.last_record and self.last_record.is_ready:
                    await self.state.initialised()
            case "awake_rt":
                result = await self._send_request()
                if result:
                    self.last_flow = result.current_flow
                    self.prev_non_null_flow = self.last_non_null_flow
                    self.last_non_null_flow = self.last_flow

        # Update counter tracking
        if self.last_record is not None:
            if self.last_flow and self.last_flow > 1:
                await self.tags.last_time_non_zero_flow.set(time.time())

            total = self.last_record.total
            last_non_zero = self.tags.last_time_non_zero_flow.value or 0
            if total is not None and time.time() - last_non_zero > (60 * 60 * 24 * 5):
                await self.tags.last_event_counter_zero.set(total)

        await self._check_for_total_alert()
        await self._check_for_pump_shutdown()

    async def _update_display_tags(self):
        await self.tags.last_flow.set(self.last_flow)
        await self.tags.comms_active.set(
            self.state.state != "sleeping" if self.state else False
        )

        if self.last_record is None:
            return

        await self.tags.last_batt_volts.set(self.last_record.battery_volts)
        await self.tags.last_solar_volts.set(self.last_record.solar_volts)
        await self.tags.last_total.set(self.last_record.total)
        await self.tags.time_last_update.set(int(time.time() - self.last_record.ts))

        total = self.last_record.total
        counter_zero = self.tags.last_event_counter_zero.value
        if total is not None and counter_zero is not None:
            await self.tags.last_event_counter.set(total - counter_zero)

    async def _check_for_total_alert(self):
        threshold = self.ui.alert_counter.value
        if self._counter_exceeds(threshold):
            await self.create_message(
                "notifications",
                {
                    "message": (
                        f"{self.app_display_name} has reached "
                        f"{threshold} ML during this event"
                    )
                },
            )
            await self.ui.alert_counter.set(None)

    async def _check_for_pump_shutdown(self):
        if not self.config.allow_shutdown.value:
            return

        threshold = self.ui.shutdown_counter.value
        if self._counter_exceeds(threshold):
            log.info(
                f"Water meter {self.app_display_name} has reached "
                f"event shutdown target of {threshold}"
            )
            await self.tags.alert_triggered.set(True)
            await self.tags.alert_message_short.set(ALERT_MESSAGE)
            await self.tags.alert_message_long.set(
                ALERT_MESSAGE_LONG.format(threshold)
            )
            await self.ui.shutdown_counter.set(None)

    async def _send_request(self):
        if time.time() - self.last_request_time < self.min_request_interval:
            log.debug("Not enough time since last request")
            return

        log.debug("Sending modbus request")
        result = await self.modbus_iface.read_registers(
            bus_id=self.config.modbus_config.name.value,
            modbus_id=self.config.modbus_id.value,
            start_address=START_REG_NUM,
            num_registers=NUM_REGS,
            register_type=REGISTER_TYPE,
        )
        if not result:
            log.info("Failed to send modbus request")
            return

        self.last_record = Record(result)
        self.last_request_time = time.time()
        return self.last_record

    def _counter_exceeds(self, value):
        if value is None or self.last_record is None:
            return False

        total = self.last_record.total
        counter_zero = self.tags.last_event_counter_zero.value

        if total is None or counter_zero is None:
            return False

        return total - counter_zero > value

    @property
    def is_pumping(self):
        max_flow = self.config.max_flow.value * 0.05
        if self.last_non_null_flow is not None and self.last_non_null_flow > max_flow:
            return True
        if self.prev_non_null_flow is not None and self.prev_non_null_flow > max_flow:
            return True
        return False

    # --- UI Handlers ---

    @ui.handler("reset_event")
    async def on_reset_event(self, ctx, value):
        total = self.last_record and self.last_record.total
        if total is None:
            log.info(
                "Failed to reset water meter event total - no last record / total."
            )
            return

        log.info(
            f"Resetting water meter event total for {self.app_display_name}"
        )
        await self.tags.last_event_counter_zero.set(total)

        await self.ui.alert_counter.set(None)
        await self.ui.shutdown_counter.set(None)

    @ui.handler("get_now")
    async def on_get_now(self, ctx, value):
        log.info("Get now action triggered")
        if self.state.state == "sleeping":
            await self.state.awaken()
