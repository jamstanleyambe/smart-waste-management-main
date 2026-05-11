"""
===========================================================================
SMART WASTE MANAGEMENT — USB Serial Bridge
===========================================================================
Connects to the ESP32 ultrasonic sensor via USB cable.
Reads JSON telemetry lines from Serial and POSTs them to Django.

The ESP32 firmware (sensor_ultrasonic.ino) automatically detects this
bridge on startup and switches to USB mode if connected, otherwise falls
back to WiFi.

USAGE:
    source venv/bin/activate
    python3 serial_bridge.py

    # Or specify a port manually:
    python3 serial_bridge.py --port /dev/cu.usbserial-0001

REQUIREMENTS:
    pip install pyserial requests
===========================================================================
"""

import serial
import serial.tools.list_ports
import requests
import json
import time
import argparse
import sys
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
DJANGO_URL      = "http://localhost:8000/api/sensor-data/"
BAUD_RATE       = 115200
HANDSHAKE_MSG   = "BRIDGE_READY\n"   # sent to ESP32 to confirm USB mode
RECONNECT_DELAY = 3                  # seconds to wait before retrying serial

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def log(tag: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{tag}] {msg}")


def find_esp32_port() -> str | None:
    """Auto-detect the ESP32 USB serial port."""
    known_chips = ["CP210", "CH340", "FTDI", "ESP32", "Silicon Labs", "USB Serial"]
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = f"{p.description} {p.manufacturer or ''}".upper()
        if any(chip.upper() in desc for chip in known_chips):
            log("USB", f"Auto-detected port: {p.device}  ({p.description})")
            return p.device

    # Fallback: return the first available USB port
    for p in ports:
        if "usb" in p.device.lower() or "cu." in p.device.lower():
            log("USB", f"Fallback port: {p.device}  ({p.description})")
            return p.device

    return None


def post_to_django(payload: dict) -> bool:
    """POST sensor JSON to Django and return True on success."""
    try:
        r = requests.post(DJANGO_URL, json=payload, timeout=5)
        if r.status_code in (200, 201):
            log("HTTP", f"✅ Saved  fill={payload.get('fill_level', '?'):.1f}%  bin={payload.get('bin_id', '?')}")
            return True
        else:
            log("HTTP", f"❌ Server returned {r.status_code}: {r.text[:120]}")
            return False
    except requests.exceptions.ConnectionError:
        log("HTTP", "❌ Django not reachable — is the server running on port 8000?")
        return False
    except Exception as e:
        log("HTTP", f"❌ Error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# MAIN BRIDGE LOOP
# ──────────────────────────────────────────────────────────────────────────────
def run_bridge(port: str):
    log("BRIDGE", f"Connecting to ESP32 on {port} at {BAUD_RATE} baud…")

    while True:
        try:
            with serial.Serial(port, BAUD_RATE, timeout=2) as ser:
                log("BRIDGE", "✅ Serial port open.  Sending handshake…")
                time.sleep(1.5)               # let ESP32 boot
                ser.write(HANDSHAKE_MSG.encode())
                ser.flush()
                log("BRIDGE", "📡 Handshake sent — ESP32 should switch to USB mode.")
                log("BRIDGE", "Listening for data… (Ctrl+C to stop)")

                while True:
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode("utf-8", errors="ignore").strip()

                    # Print all ESP32 serial output so you can debug easily
                    if line:
                        print(f"  ESP32 → {line}")

                    # Only process lines that look like JSON sensor payloads
                    if not line.startswith("{"):
                        continue

                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Must have at minimum bin_id and fill_level
                    if "bin_id" not in payload or "fill_level" not in payload:
                        continue

                    # Force signal_strength to -1 when in USB mode (no WiFi)
                    payload.setdefault("signal_strength", -1)

                    post_to_django(payload)

        except serial.SerialException as e:
            log("USB", f"❌ Serial error: {e}")
            log("USB", f"Retrying in {RECONNECT_DELAY}s…")
            time.sleep(RECONNECT_DELAY)
        except KeyboardInterrupt:
            log("BRIDGE", "Stopped by user.")
            sys.exit(0)


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Waste USB Serial Bridge")
    parser.add_argument("--port", help="Serial port (e.g. /dev/cu.usbserial-0001)")
    parser.add_argument("--url",  default=DJANGO_URL, help="Django API endpoint")
    args = parser.parse_args()

    DJANGO_URL = args.url

    port = args.port or find_esp32_port()
    if not port:
        log("USB", "❌ No ESP32 found.  Plug in the USB cable and try again.")
        log("USB", "   Or run:  python3 serial_bridge.py --port /dev/cu.XXXX")
        sys.exit(1)

    run_bridge(port)
