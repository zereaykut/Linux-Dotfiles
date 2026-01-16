#!/usr/bin/python

import subprocess as sp
import time

import psutil

BATTERY_CRITICAL = 20
BATTERY_URGENT = 30
BATTERY_NOTIFY_ID = 92999

CHARGE_PLUG_NOTIFY_ID = 92998


def secs2hours(secs: int) -> str:
    mm, ss = divmod(secs, 60)
    hh, mm = divmod(mm, 60)
    return "%d:%02d:%02d" % (hh, mm, ss)


def get_battery_info() -> dict:
    battery_info = psutil.sensors_battery()
    return {
        "percent": round(battery_info.percent, 2),
        "secsleft": secs2hours(battery_info.secsleft),
        "power_plugged": battery_info.power_plugged,
    }


def send_notification(
    message: str, icon: str, notify_id: int, timeout: int = 800, urgency: str = "normal"
) -> None:
    sp.run(
        f"""notify-send "{message}" -i {icon} -r {notify_id} -t {timeout} -u {urgency}""",
        shell=True,
    )


if __name__ == "__main__":
    user = sp.run("whoami", shell=True, capture_output=True, text=True).stdout.strip()

    battery_info = get_battery_info()
    plugged_ = battery_info["power_plugged"]

    while True:
        battery_info = get_battery_info()
        plugged = battery_info["power_plugged"]
        if (battery_info["percent"] <= BATTERY_URGENT) & (not plugged):
            send_notification(
                f"""Percentage: {battery_info["percent"]}%\nPlugged:{battery_info["power_plugged"]}""",
                f"/home/{user}/.config/dunst/icons/status/battery-status.png",
                BATTERY_NOTIFY_ID,
                10000,
                "normal",
            )
        elif (battery_info["percent"] <= BATTERY_CRITICAL) & (not plugged):
            send_notification(
                f"""Percentage: {battery_info["percent"]}%\nPlugged:{battery_info["power_plugged"]}""",
                f"/home/{user}/.config/dunst/icons/status/battery-status.png",
                BATTERY_NOTIFY_ID,
                10000,
                "critical",
            )

        if plugged_ != plugged:
            if plugged:
                send_notification(
                    f"""Charge Plugged""",
                    f"/home/{user}/.config/dunst/icons/status/charger-plugged.svg",
                    CHARGE_PLUG_NOTIFY_ID,
                    5000,
                    "normal",
                )
            else:
                send_notification(
                    f"""Charge Unplugged""",
                    f"/home/{user}/.config/dunst/icons/status/charger-not-plugged.svg",
                    CHARGE_PLUG_NOTIFY_ID,
                    5000,
                    "normal",
                )
            plugged_ = plugged

        time.sleep(1)
