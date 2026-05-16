import lvgl as lv
from mpos import Activity, Intent, print_event, sdcard, ui
from action_activity import ActionActivity

class FileManager(Activity):

    # Widgets:
    file_explorer = None

    def onCreate(self):
        sdcard.mount_with_optional_format('/sdcard')
        #lv.log_register_print_cb(self.log_callback)
        screen = lv.obj()
        self.file_explorer = lv.file_explorer(screen)
        self.file_explorer.explorer_open_dir('M:/')
        self.file_explorer.align(lv.ALIGN.CENTER, 0, 0)
        self.file_explorer.add_event_cb(self.file_explorer_event_cb, lv.EVENT.ALL, None)
        self.file_explorer.explorer_set_quick_access_path(lv.EXPLORER.HOME_DIR, "M:/home/user/")
        self.file_explorer.explorer_set_quick_access_path(lv.EXPLORER.PICTURES_DIR, "M:/data/images/")

        file_table = self.file_explorer.explorer_get_file_table()
        file_table.add_event_cb(lambda e: print("FileManager: long press detected"), lv.EVENT.LONG_PRESSED, None)
        self.setContentView(screen)

    def onResume(self, screen):
        sdcard.mount_with_optional_format('/sdcard')

    def file_explorer_event_cb(self, event):
        print_event(event)
        event_code = event.get_code()
        if event_code == lv.EVENT.VALUE_CHANGED:
            path = self.file_explorer.explorer_get_current_path()
            clean_path = path[2:] if path[1] == ':' else path
            file = self.file_explorer.explorer_get_selected_file_name()
            fullpath = f"{clean_path}{file}"
            print(f"Selected: {fullpath}")
            self.startActivity(Intent(activity_class=ActionActivity).putExtra("path", fullpath))

    # Custom log callback to capture FPS
    def log_callback(self, level, log_str):
        # Convert log_str to string if it's a bytes object
        log_str = log_str.decode() if isinstance(log_str, bytes) else log_str
        print(f"Level: {level}, Log: {log_str}")
