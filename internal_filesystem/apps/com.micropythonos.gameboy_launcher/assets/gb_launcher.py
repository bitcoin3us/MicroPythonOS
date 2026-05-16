from mpos import Activity, Intent
from retrogo_launcher import RetroGoLauncher


class GameboyLauncher(Activity):

    def onCreate(self):
        self.startActivity(
            Intent(activity_class=RetroGoLauncher)
            .putExtra("title", "Choose your Gameboy ROM:")
            .putExtra("roms_subdir", "gb")
            .putExtra("partition_label", "retro-core")
            .putExtra("boot_name", "gb")
            .putExtra("game_name", "GB")
            .putExtra("file_extensions", (".gb", ".gbc", ".zip"))
        )
