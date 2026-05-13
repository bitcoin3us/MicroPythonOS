import lvgl as lv
import os
from mpos import Activity, Intent, SettingsActivity, SettingActivity, SharedPreferences, TaskManager, sdcard


class RetroGoLauncher(Activity):

    mountpoint_sdcard = "/sdcard"
    esp32_partition_type_ota_0 = 16

    def onCreate(self):
        intent = self.getIntent()
        extras = intent.extras if intent else {}

        self.title = extras.get("title", "Choose file:")
        self.roms_subdir = extras.get("roms_subdir")
        self.partition_label = extras.get("partition_label")
        self.boot_name = extras.get("boot_name")
        self.game_name = extras.get("game_name", "Game")
        self.file_extensions = extras.get("file_extensions", (".wad", ".zip"))

        self.romdir = "/roms"
        self.gamedir = self.romdir + "/" + self.roms_subdir
        self.retrogodir = "/retro-go"
        self.configdir = self.retrogodir + "/config"
        self.bootfile = self.configdir + "/boot.json"
        self.current_subdir = ""

        screen = lv.obj()
        screen.set_style_pad_all(15, lv.PART.MAIN)

        title_label = lv.label(screen)
        title_label.set_text(self.title)
        title_label.align(lv.ALIGN.TOP_LEFT, 0, 0)

        self.wadlist = lv.list(screen)
        self.wadlist.set_size(lv.pct(100), lv.pct(70))
        self.wadlist.center()

        self.settings_button = lv.button(screen)
        settings_margin = 15
        settings_size = 44
        self.settings_button.set_size(settings_size, settings_size)
        self.settings_button.align(lv.ALIGN.TOP_RIGHT, -settings_margin, 10)
        self.settings_button.add_event_cb(self.settings_button_tap, lv.EVENT.CLICKED, None)
        settings_label = lv.label(self.settings_button)
        settings_label.set_text(lv.SYMBOL.SETTINGS)
        settings_label.set_style_text_font(lv.font_montserrat_24, lv.PART.MAIN)
        settings_label.center()
        self.settings_button.move_to_index(-1)

        self.status_label = lv.label(screen)
        self.status_label.set_width(lv.pct(90))
        self.status_label.set_long_mode(lv.label.LONG_MODE.WRAP)
        self.status_label.align(lv.ALIGN.BOTTOM_LEFT, 0, 0)
        self.status_label.set_style_text_color(lv.color_hex(0x00FF00), lv.PART.MAIN)

        self.setContentView(screen)

    def onResume(self, screen):
        self.bootfile_prefix = ""
        mounted_sdcard = sdcard.mount_with_optional_format(self.mountpoint_sdcard)
        if mounted_sdcard:
            print("sdcard is mounted, configuring it...")
            self.bootfile_prefix = self.mountpoint_sdcard
        self.bootfile_to_write = self.bootfile_prefix + self.bootfile
        print(f"writing to {self.bootfile_to_write}")

        self.refresh_file_list()

    def scan_subdirs(self, directory):
        subdirs = []
        try:
            for entry in os.listdir(directory):
                if entry.startswith("."):
                    continue
                full = directory + "/" + entry
                try:
                    if os.stat(full)[0] & 0x4000:
                        subdirs.append(entry)
                except Exception:
                    pass
            subdirs.sort()
        except OSError:
            pass
        except Exception as e:
            print(f"Error scanning subdirectories in {directory}: {e}")
        return subdirs

    def scan_files(self, directory):
        matching_files = []
        try:
            for filename in os.listdir(directory):
                if filename.lower().endswith(self.file_extensions):
                    matching_files.append(filename)
            matching_files.sort()
            print(f"Found {len(matching_files)} files in {directory}: {matching_files}")
        except OSError as e:
            print(f"Directory does not exist or cannot be read: {directory}")
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")
        return matching_files

    def get_file_size_warning(self, filepath):
        try:
            size = os.stat(filepath)[6]
            if size == 0:
                return " (EMPTY FILE)"
            elif size < 80 * 1024:
                return " (TOO SMALL)"
        except Exception as e:
            print(f"Error checking file size for {filepath}: {e}")
        return ""

    def refresh_file_list(self):
        current_full_dir = self.bootfile_prefix + self.gamedir
        if self.current_subdir:
            current_full_dir += "/" + self.current_subdir

        self.status_label.set_text(f"Listing: {current_full_dir}")
        print(f"refresh_file_list: Clearing current list (dir={self.current_subdir})")
        self.wadlist.clean()

        subdirs = self.scan_subdirs(current_full_dir)
        all_files = self.scan_files(current_full_dir)

        if not subdirs and not all_files:
            self.status_label.set_text(f"No files found in {current_full_dir}")
            print("No files found")
            return

        print(f"refresh_file_list: {len(subdirs)} dirs, {len(all_files)} files")

        if self.current_subdir:
            button = self.wadlist.add_button(None, "..")
            button.add_event_cb(lambda e: self.navigate_up(), lv.EVENT.CLICKED, None)

        for d in subdirs:
            button = self.wadlist.add_button(None, d + "/")
            button.add_event_cb(lambda e, dirname=d: self.navigate_into(dirname), lv.EVENT.CLICKED, None)

        for f in all_files:
            fullpath = self.gamedir + "/" + self.current_subdir + "/" + f if self.current_subdir else self.gamedir + "/" + f
            warning = self.get_file_size_warning(current_full_dir + "/" + f)
            button_text = f + warning
            button = self.wadlist.add_button(None, button_text)
            button.add_event_cb(
                lambda e, p=fullpath: TaskManager.create_task(self.start_game(self.bootfile_prefix, self.bootfile_to_write, p)),
                lv.EVENT.CLICKED, None
            )

    def navigate_into(self, subdir):
        if self.current_subdir:
            self.current_subdir += "/" + subdir
        else:
            self.current_subdir = subdir
        self.refresh_file_list()

    def navigate_up(self):
        if not self.current_subdir:
            return
        parts = self.current_subdir.split("/")
        parts.pop()
        self.current_subdir = "/".join(parts)
        self.refresh_file_list()

    def settings_button_tap(self, event):
        global_json_path = self.bootfile_prefix + self.retrogodir + "/config/global.json"
        current_audio = "buzzer"
        current_volume = "50"
        try:
            import json
            fd = open(global_json_path, "r")
            config = json.load(fd)
            fd.close()
            if config.get("AudioDriver") == "i2s":
                current_audio = "i2s"
            current_volume = str(config.get("Volume", 50))
        except Exception:
            pass

        prefs = SharedPreferences(self.appFullName)
        intent = Intent(activity_class=SettingsActivity)
        intent.putExtra("prefs", prefs)
        intent.putExtra("settings", [
            {
                "title": "Audio out",
                "key": "audio_output",
                "ui": "radiobuttons",
                "dont_persist": True,
                "default_value": current_audio,
                "ui_options": [
                    ("Buzzer", "buzzer"),
                    ("Ext DAC", "i2s"),
                ],
                "changed_callback": self._apply_audio_output,
            },
            {
                "title": "Volume",
                "key": "audio_volume",
                "ui": "slider",
                "dont_persist": True,
                "default_value": current_volume,
                "min": 0,
                "max": 100,
                "changed_callback": self._apply_volume,
            },
        ])
        self.startActivity(intent)

    def _apply_audio_output(self, new_value):
        import json
        global_json_path = self.bootfile_prefix + self.retrogodir + "/config/global.json"
        config = {}
        try:
            fd = open(global_json_path, "r")
            config = json.load(fd)
            fd.close()
        except Exception:
            pass
        if new_value == "buzzer":
            config["AudioDriver"] = "buzzer"
            config["AudioDevice"] = 0
        elif new_value == "i2s":
            config["AudioDriver"] = "i2s"
            config["AudioDevice"] = 1
        try:
            fd = open(global_json_path, "w")
            json.dump(config, fd)
            fd.close()
        except Exception as e:
            print(f"Error writing {global_json_path}: {e}")

    def _apply_volume(self, new_value):
        import json
        try:
            vol = int(new_value)
            if vol < 0:
                vol = 0
            elif vol > 100:
                vol = 100
        except (ValueError, TypeError):
            print(f"Invalid volume value: {new_value}")
            return
        global_json_path = self.bootfile_prefix + self.retrogodir + "/config/global.json"
        config = {}
        try:
            fd = open(global_json_path, "r")
            config = json.load(fd)
            fd.close()
        except Exception:
            pass
        config["Volume"] = vol
        try:
            fd = open(global_json_path, "w")
            json.dump(config, fd)
            fd.close()
        except Exception as e:
            print(f"Error writing {global_json_path}: {e}")

    def mkdir(self, dirname):
        try:
            os.mkdir(dirname)
        except Exception as e:
            print(f"Info: could not create directory {dirname} because: {e}")

    async def start_game(self, bootfile_prefix, bootfile_to_write, gamefile):
        self.status_label.set_text(f"Launching {self.game_name} with file: {bootfile_prefix}{gamefile}")
        await TaskManager.sleep(1)

        self.mkdir(bootfile_prefix + self.romdir)
        self.mkdir(bootfile_prefix + self.gamedir)
        self.mkdir(bootfile_prefix + self.retrogodir)
        self.mkdir(bootfile_prefix + self.configdir)

        try:
            import json
            fd = open(bootfile_to_write, "w")
            bootconfig = {
                "BootName": self.boot_name,
                "BootArgs": f"/sd{gamefile}",
                "BootSlot": -1,
                "BootFlags": 0
            }
            print(f"Writing boot config: {bootconfig}")
            json.dump(bootconfig, fd)
            fd.close()
        except Exception as e:
            self.status_label.set_text(f"ERROR: could not write config file: {e}")
            return

        results = []
        try:
            from esp32 import Partition
            results = Partition.find(label=self.partition_label)
        except Exception as e:
            self.status_label.set_text(f"ERROR: could not search for internal partition with label {self.partition_label}, unable to start: {e}")
            return

        if len(results) < 1:
            self.status_label.set_text(f"ERROR: could not find internal partition with label {self.partition_label}, unable to start")
            return

        partition = results[0]
        try:
            partition.set_boot()
        except Exception as e:
            print(f"ERROR: could not set partition {partition} as boot, it probably doesn't contain a valid program: {e}")

        try:
            import vfs
            vfs.umount("/")
        except Exception as e:
            print(f"Warning: could not unmount internal filesystem from /: {e}")

        try:
            from esp32 import NVS
            nvs = NVS("fri3d.sys")
            boot_partition = nvs.get_i32("boot_partition")
            print(f"boot_partition in fri3d.sys of NVS: {boot_partition}")
            running_partition = Partition(Partition.RUNNING)
            running_partition_nr = running_partition.info()[1] - self.esp32_partition_type_ota_0
            print(f"running_partition_nr: {running_partition_nr}")
            if running_partition_nr != boot_partition:
                print(f"setting boot_partition in fri3d.sys of NVS to {running_partition_nr}")
                nvs.set_i32("boot_partition", running_partition_nr)
            else:
                print("No need to update boot_partition")
        except Exception as e:
            print(f"Warning: could not write currently booted partition to boot_partition in fri3d.sys of NVS: {e}")

        # Wait a few seconds so the user has time to switch off the device in the "boot to retro-go" state
        # This is useful to capture debug logging, as this triggers a re-init of the USB-to-serial.
        self.status_label.set_text("Starting in 3 seconds...")
        await TaskManager.sleep(3)

        try:
            import machine
            machine.reset()
        except Exception as e:
            print(f"Warning: could not restart machine: {e}")
