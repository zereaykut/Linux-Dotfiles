#!/usr/bin/python
import json
import subprocess as sp


class HyprlandClient:
    def __init__(self):
        self.user = sp.run(["whoami"], capture_output=True, text=True).stdout.strip()
        self.windows = self.get_windows_info()
        self.rofi_list = self.preprocess_data()

    def get_windows_info(self):
        windows = sp.run(["hyprctl", "clients", "-j"], capture_output=True, text=True)
        return json.loads(windows.stdout)

    def preprocess_data(self):
        rofi_list = []
        for window in self.windows:
            if window["class"]:
                ws_ = window["workspace"]["name"]
                class_ = window["class"]
                if class_.startswith("org"):
                    class_ = class_.split(".")[-1]
                title_ = window["title"]
                address_ = window["address"]
                rofi_list.append(
                    {"ws": ws_, "class": class_, "title": title_, "address": address_}
                )
        return sorted(rofi_list, key=lambda x: x["ws"])

    def create_rofi_output(self):
        rofi_output = ""
        for window in self.rofi_list:
            # entry = f"ws {window.get('ws')} | {window.get('class')} <> {window.get('title')}   || {window.get('address')}"
            workspace = window.get("ws")
            window_class = window.get("class")
            window_title = window.get("title")
            if len(window_title) > 40:
                window_title = window_title[:40] + "..."
            address = window.get("address")

            entry = f"ws {workspace:^2} | {window_class:<20} <> {window_title:<45}   || {address:^10}"
            
            if not rofi_output:
                rofi_output = entry
            else:
                rofi_output = f"{rofi_output}\n{entry}"
        return rofi_output

    def get_rofi_selection(self, rofi_output):
        rofi_select = sp.run(
            f"""echo "{rofi_output}" | rofi -dmenu -matching normal -i -config /home/{self.user}/.config/rofi/selector.rasi""",
            shell=True,
            capture_output=True,
            text=True,
        )
        return rofi_select.stdout.split("||")[-1].strip()

    def focus_window(self, address):
        sp.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"])

    def run(self):
        rofi_output = self.create_rofi_output()
        selected_address = self.get_rofi_selection(rofi_output)
        self.focus_window(selected_address)


if __name__ == "__main__":
    client = HyprlandClient()
    client.run()
