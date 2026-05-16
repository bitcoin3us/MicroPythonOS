import os
import lvgl as lv
from mpos import Activity, print_event, sdcard


class FileManager(Activity):

    _action_bar = None
    _selected_path = None
    _current_path = None
    _list = None
    _path_label = None

    def onCreate(self):
        sdcard.mount_with_optional_format("/sdcard")
        screen = lv.obj()
        screen.set_flex_flow(lv.FLEX_FLOW.COLUMN)

        self._path_label = lv.label(screen)
        self._path_label.set_width(lv.pct(100))
        self._path_label.set_style_pad_all(6, lv.PART.MAIN)

        self._list = lv.list(screen)
        self._list.set_size(lv.pct(100), lv.pct(100))

        self._populate_dir("/home/user/")
        self.setContentView(screen)

    def onResume(self, screen):
        sdcard.mount_with_optional_format("/sdcard")

    def _populate_dir(self, path):
        self._dismiss_action_bar()
        self._list.clean()
        path = path.rstrip("/") + "/"
        self._current_path = path
        self._path_label.set_text("  " + path)

        if path != "/":
            parent = "/".join(path.rstrip("/").split("/")[:-1]) + "/"
            btn = self._list.add_button(None, lv.SYMBOL.LEFT + "  ..")
            btn.add_event_cb(lambda e, p=parent: self._populate_dir(p), lv.EVENT.CLICKED, None)

        try:
            items = os.listdir(path)
        except OSError:
            return

        dirs = []
        files = []
        for item in items:
            full = path + item
            try:
                if os.stat(full)[0] & 0x4000:
                    dirs.append(item)
                else:
                    files.append(item)
            except OSError:
                files.append(item)

        dirs.sort()
        files.sort()

        for d in dirs:
            fullpath = path + d + "/"
            btn = self._list.add_button(None, lv.SYMBOL.DIRECTORY + "  " + d)
            btn.add_event_cb(lambda e, p=fullpath: self._populate_dir(p), lv.EVENT.CLICKED, None)
            btn.add_event_cb(lambda e, p=fullpath: self._on_list_long_press(p), lv.EVENT.LONG_PRESSED, None)

        for f in files:
            fullpath = path + f
            btn = self._list.add_button(None, lv.SYMBOL.FILE + "  " + f)
            btn.add_event_cb(lambda e, p=fullpath: self._on_list_long_press(p), lv.EVENT.LONG_PRESSED, None)

    def _on_list_long_press(self, path):
        print(f"FileManager: long press on {path}")
        self._selected_path = path
        self._show_action_bar()

    def _show_action_bar(self):
        self._dismiss_action_bar()
        screen = lv.screen_active()
        bar = lv.obj(screen)
        bar.add_flag(lv.obj.FLAG.FLOATING)
        bar.set_size(lv.pct(100), 60)
        bar.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        bar.set_style_bg_color(lv.color_hex(0x444444), lv.PART.MAIN)
        bar.set_style_pad_all(8, lv.PART.MAIN)
        bar.set_flex_flow(lv.FLEX_FLOW.ROW)
        bar.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        delete_btn = lv.button(bar)
        lv.label(delete_btn).set_text("Delete")
        delete_btn.add_event_cb(lambda e: self._delete_selected(), lv.EVENT.CLICKED, None)

        rename_btn = lv.button(bar)
        lv.label(rename_btn).set_text("Rename")
        rename_btn.add_event_cb(lambda e: self._show_rename_ui(), lv.EVENT.CLICKED, None)

        cancel_btn = lv.button(bar)
        lv.label(cancel_btn).set_text("Cancel")
        cancel_btn.add_event_cb(lambda e: self._dismiss_action_bar(), lv.EVENT.CLICKED, None)

        self._action_bar = bar

    def _dismiss_action_bar(self):
        if self._action_bar:
            self._action_bar.delete()
            self._action_bar = None

    def _delete_selected(self):
        path = self._selected_path
        try:
            os.remove(path)
        except OSError:
            try:
                os.rmdir(path.rstrip("/"))
            except OSError as e:
                print(f"FileManager: delete error {path}: {e}")
        print(f"FileManager: deleted {path}")
        self._dismiss_action_bar()
        self._populate_dir(self._current_path)

    def _show_rename_ui(self):
        bar = self._action_bar
        if not bar:
            return
        bar.clean()
        old_name = self._selected_path.rstrip("/").split("/")[-1]
        ta = lv.textarea(bar)
        ta.set_text(old_name)
        ta.set_width(130)
        confirm_btn = lv.button(bar)
        lv.label(confirm_btn).set_text("Confirm")
        confirm_btn.add_event_cb(lambda e: self._confirm_rename(ta.get_text()), lv.EVENT.CLICKED, None)
        cancel_btn = lv.button(bar)
        lv.label(cancel_btn).set_text("Back")
        cancel_btn.add_event_cb(lambda e: self._show_action_bar(), lv.EVENT.CLICKED, None)

    def _confirm_rename(self, new_name):
        path = self._selected_path
        dir_part = "/".join(path.rstrip("/").split("/")[:-1])
        new_path = f"{dir_part}/{new_name}"
        try:
            os.rename(path, new_path)
            print(f"FileManager: renamed {path} -> {new_path}")
        except OSError as e:
            print(f"FileManager: rename error {path} -> {new_path}: {e}")
        self._dismiss_action_bar()
        self._populate_dir(self._current_path)
