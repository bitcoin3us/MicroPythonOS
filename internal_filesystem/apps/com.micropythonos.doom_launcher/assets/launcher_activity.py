import lvgl as lv
import os
from mpos import Activity, TaskManager, sdcard


class LauncherActivity(Activity):

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

        screen = lv.obj()
        screen.set_style_pad_all(15, lv.PART.MAIN)

        title_label = lv.label(screen)
        title_label.set_text(self.title)
        title_label.align(lv.ALIGN.TOP_LEFT, 0, 0)

        self.wadlist = lv.list(screen)
        self.wadlist.set_size(lv.pct(100), lv.pct(70))
        self.wadlist.center()

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
        self.status_label.set_text(f"Listing files in: {self.bootfile_prefix + self.gamedir}")
        print("refresh_file_list: Clearing current list")
        self.wadlist.clean()

        all_files = self.scan_files(self.bootfile_prefix + self.gamedir)

        if len(all_files) == 0:
            self.status_label.set_text(f"No files found in {self.gamedir}")
            print("No files found")
            return

        print(f"refresh_file_list: Populating list with {len(all_files)} files")
        self.status_label.set_text(f"Listed files in: {self.bootfile_prefix + self.gamedir}")
        for f in all_files:
            warning = self.get_file_size_warning(self.bootfile_prefix + self.gamedir + "/" + f)
            button_text = f + warning
            button = self.wadlist.add_button(None, button_text)
            button.add_event_cb(
                lambda e, p=self.gamedir + "/" + f: TaskManager.create_task(self.start_game(self.bootfile_prefix, self.bootfile_to_write, p)),
                lv.EVENT.CLICKED, None
            )

        if len(all_files) == 1:
            print(f"refresh_file_list: Only one file found, auto-starting: {all_files[0]}")
            TaskManager.create_task(self.start_game(self.bootfile_prefix, self.bootfile_to_write, self.gamedir + "/" + all_files[0]))

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

        try:
            import machine
            machine.reset()
        except Exception as e:
            print(f"Warning: could not restart machine: {e}")
