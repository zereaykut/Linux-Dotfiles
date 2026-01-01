#!/usr/bin/python
import json
import subprocess as sp


class NiriClient:
    def __init__(self):
        self.user = (
            sp.run(["whoami"], capture_output=True, text=True).stdout.strip()
        )
        self.windows = self.get_windows_info()
        self.rofi_list = self.preprocess_data()

    def get_windows_info(self):
        """Niri pencerelerini getirir."""
        windows = sp.run(["niri", "msg", "-j", "windows"], capture_output=True, text=True)
        return json.loads(windows.stdout)

    def preprocess_data(self):
        rofi_list = []
        
        for window in self.windows:
            app_id = window.get("app_id", "")
            title = window.get("title", "")
            ws = window.get("workspace_id", "")
            id = window.get("id", "")
            
            if app_id:
                # app_id uzun olabiliyor (Firefox: "org.mozilla.firefox")
                short_class = app_id.split(".")[-1] if app_id.startswith("org.") else app_id
    
                rofi_list.append(
                    {"ws": ws, "class": short_class, "title": title, "id": id}
                )

        # Workspace sıralaması
        return sorted(rofi_list, key=lambda x: str(x["ws"]))

    def create_rofi_output(self):
        rofi_output = ""

        for window in self.rofi_list:
            ws = window["ws"]
            window_class = window["class"]
            title = window["title"]
            if len(title) > 40:
                title = title[:40] + "..."

            id = window["id"]

            entry = f"ws {ws:^2} | {window_class:<20} <> {title:<45}   || {id:^10}"

            rofi_output += entry + "\n"

        return rofi_output.strip()

    def get_rofi_selection(self, rofi_output):
        rofi_select = sp.run(
            f"""echo "{rofi_output}" | rofi -dmenu -matching normal -i -config /home/{self.user}/.config/rofi/selector.rasi""",
            shell=True,
            capture_output=True,
            text=True,
        )
        return rofi_select.stdout.split("||")[-1].strip()

    def focus_window(self, id):
        sp.run(["niri", "msg", "action", "focus-window", "--id", id])

    def run(self):
        rofi_output = self.create_rofi_output()
        selected_id = self.get_rofi_selection(rofi_output)

        if selected_id:
            self.focus_window(selected_id)


if __name__ == "__main__":
    client = NiriClient()
    client.run()
