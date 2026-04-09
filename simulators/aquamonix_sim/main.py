"""
A module to recreate a modbus interface to an Aquamonix i500 series flow meter.
"""

import asyncio
import logging
import os
import random
import time

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartAsyncTcpServer

from transitions import Machine, State

log = logging.getLogger()


def add_noise(in_num, stdev=5):
    return in_num + ((random.random() - 0.5) * stdev)


class CustomSlaveContext(ModbusSlaveContext):
    def __init__(self, on_read_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_read_callback = on_read_callback

    def getValues(self, fx, address, count=1):
        self.on_read_callback()
        return super().getValues(fx, address, count)


class AquamonixSimulator:
    states = [
        State(name="sleeping", on_enter=["save_current_state_enter_time"]),
        State(name="awake_init", on_enter=["save_current_state_enter_time"]),
        State(name="awake_rt", on_enter=["save_current_state_enter_time"]),
    ]

    transitions = [
        {"trigger": "awaken", "source": "sleeping", "dest": "awake_init"},
        {"trigger": "initialised", "source": "awake_init", "dest": "awake_rt"},
        {"trigger": "goto_sleep", "source": "awake_rt", "dest": "sleeping"},
    ]

    def __init__(self, device_id: int, host: str, port: int):
        self.device_id = device_id
        self.host = host
        self.port = port

        self.current_flow_megs = 160
        self.last_output_flow_megs = self.current_flow_megs

        self.last_totals_update_time = time.time()
        self.current_peak_total = 73495  # kilolitres
        self.current_off_peak_total = 1256  # kilolitres

        self.last_context_read = None
        self.context = None
        self.is_ready = asyncio.Event()

        self.setup_state_machine()

    def setup_state_machine(self):
        self.sm = Machine(
            model=self,
            states=self.states,
            transitions=self.transitions,
            initial="sleeping",
        )

    def save_current_state_enter_time(self):
        self.current_state_enter_time = time.time()

    def get_time_in_state(self):
        return time.time() - self.current_state_enter_time

    def on_read_callback(self):
        self.last_context_read = time.time()

    async def start_modbus_server(self):
        """Start a TCP Modbus Server."""
        store = self.context = CustomSlaveContext(
            on_read_callback=self.on_read_callback,
            di=ModbusSequentialDataBlock(0x00, [17] * 100),
            co=ModbusSequentialDataBlock(0x00, [17] * 100),
            hr=ModbusSequentialDataBlock(0x00, [0] * 100),
            ir=ModbusSequentialDataBlock(0x00, [17] * 100),
        )

        context = ModbusServerContext(slaves=store, single=True)
        identity = ModbusDeviceIdentification(
            info_name={
                "VendorName": "Doover",
                "ProductCode": "AQSIM",
                "VendorUrl": "https://doover.com",
                "ProductName": "Aquamonix Simulator",
                "ModelName": "i500 Series Flow Meter Sim",
                "MajorMinorRevision": "1.0.0",
            }
        )

        self.is_ready.set()
        return await StartAsyncTcpServer(
            context=context,
            identity=identity,
            address=(self.host, self.port),
            framer="socket",
        )

    def set_register(self, reg: int, value: int):
        log.debug(f"Setting register {reg} to {value}")
        return self.context.setValues(0x03, reg, [int(value)])

    @staticmethod
    def megs_per_day_to_l_per_sec(in_val):
        return (in_val * 1000000) / (60 * 60 * 24)

    @staticmethod
    def get_higher_word(in_val):
        return int(in_val) >> 16

    @staticmethod
    def get_lower_word(in_val):
        return int(in_val) & 0xFFFF

    def update_totals(self):
        curr_time = time.time()
        dt = curr_time - self.last_totals_update_time

        curr_flow_l_sec = self.megs_per_day_to_l_per_sec(self.current_flow_megs)
        dv = curr_flow_l_sec * 1000 * dt  # kilolitres to add to totals

        self.current_peak_total = self.current_peak_total + dv
        self.current_off_peak_total = self.current_off_peak_total + dv

        self.last_totals_update_time = curr_time

    def generate_output_values(self, target_flow: int):
        if self.state == "awake_rt":
            pipe_full_gate_control_ec_status = 5  # 0000000000000101
            self.set_register(23, pipe_full_gate_control_ec_status)

            self.last_output_flow_megs = add_noise(target_flow, 0.5)
            l_per_sec_flow = self.megs_per_day_to_l_per_sec(self.last_output_flow_megs)
            self.set_register(29, l_per_sec_flow)

            batt_mvolts = add_noise(127, 0.5)
            self.set_register(30, batt_mvolts)

            solar_mvolts = add_noise(185, 0.5)
            self.set_register(31, solar_mvolts)

            self.update_totals()

            peak_high16 = self.get_higher_word(self.current_peak_total)
            self.set_register(32, peak_high16)
            peak_low16 = self.get_lower_word(self.current_peak_total)
            self.set_register(33, peak_low16)

            off_peak_high16 = self.get_higher_word(self.current_off_peak_total)
            self.set_register(34, off_peak_high16)
            off_peak_low16 = self.get_lower_word(self.current_off_peak_total)
            self.set_register(35, off_peak_low16)

            self.set_register(41, 0)

        else:
            if self.state == "awake_init":
                pipe_full_gate_control_ec_status = 5
                self.set_register(23, pipe_full_gate_control_ec_status)
            else:
                self.set_register(23, 0)

            self.last_output_flow_megs = 0
            for reg in range(29, 36):
                self.set_register(reg, 0)

            self.set_register(41, 1)

    async def main_loop(self):
        self.generate_output_values(self.current_flow_megs)
        log.info(f"{time.time()} - {self.state} - Flow={self.last_output_flow_megs}")

        match self.state:
            case "awake_rt":
                if self.last_context_read is not None:
                    self.last_context_read = None
                    self.save_current_state_enter_time()

                if self.get_time_in_state() > 120:
                    self.goto_sleep()
                    self.last_context_read = None

            case "awake_init":
                if self.get_time_in_state() > 20:
                    self.initialised()

            case "sleeping":
                if self.last_context_read is not None:
                    self.last_context_read = None
                    self.awaken()

    async def run(self):
        errors = 0
        log.info("Starting...")
        t = asyncio.create_task(self.start_modbus_server())

        while True:
            if t.done():
                raise RuntimeError("Modbus server failed.")

            await self.is_ready.wait()
            try:
                await self.main_loop()
                errors = 0
            except Exception as e:
                errors += 1
                if errors > 5:
                    log.error("Too many errors, exiting.")
                    break

                log.error(f"Error in main loop: {e}. Sleeping and retrying...")
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(1)


if __name__ == "__main__":
    sim = AquamonixSimulator(
        int(os.environ.get("DEVICE_ID", 1)),
        os.environ.get("MODBUS_HOST", "127.0.0.1"),
        int(os.environ.get("MODBUS_PORT", 5020)),
    )
    logging.basicConfig(
        level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO
    )
    asyncio.run(sim.run())
