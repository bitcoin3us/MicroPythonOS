from mpos import Activity, Intent
from launcher_activity import RetroGoLauncher


class NesLauncher(Activity):

    def onCreate(self):
        self.startActivity(
            Intent(activity_class=RetroGoLauncher)
            .putExtra("title", "Choose your NES ROM:")
            .putExtra("roms_subdir", "nes")
            .putExtra("partition_label", "retro-core")
            .putExtra("boot_name", "nes")
            .putExtra("game_name", "NES")
            .putExtra("file_extensions", (".nes", ".fc", ".fds", ".nsf", ".zip"))
        )
