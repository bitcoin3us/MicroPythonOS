import lvgl as lv
import os
from mpos import Activity


class ActionActivity(Activity):

    def onCreate(self):
        self._path = self.getIntent().extras.get("path")
        screen = lv.obj()

        path_label = lv.label(screen)
        path_label.set_text(self._path)
        path_label.set_width(lv.pct(90))
        path_label.align(lv.ALIGN.TOP_MID, 0, 10)

        self._delete_btn = lv.button(screen)
        lv.label(self._delete_btn).set_text("Delete")
        self._delete_btn.add_event_cb(lambda e: self.delete_cb(), lv.EVENT.CLICKED, None)
        self._delete_btn.align(lv.ALIGN.CENTER, 0, -40)

        self._rename_btn = lv.button(screen)
        lv.label(self._rename_btn).set_text("Rename")
        self._rename_btn.add_event_cb(lambda e: self.show_rename_ui(), lv.EVENT.CLICKED, None)
        self._rename_btn.align(lv.ALIGN.CENTER, 0, 20)

        name_part = self._path.rstrip('/').split('/')[-1]
        self._rename_ta = lv.textarea(screen)
        self._rename_ta.set_text(name_part)
        self._rename_ta.set_width(lv.pct(80))
        self._rename_ta.align(lv.ALIGN.CENTER, 0, -20)
        self._rename_ta.add_flag(lv.obj.FLAG.HIDDEN)

        self._confirm_btn = lv.button(screen)
        lv.label(self._confirm_btn).set_text("Confirm")
        self._confirm_btn.add_event_cb(lambda e: self.confirm_rename(), lv.EVENT.CLICKED, None)
        self._confirm_btn.align(lv.ALIGN.CENTER, 0, 30)
        self._confirm_btn.add_flag(lv.obj.FLAG.HIDDEN)

        self._cancel_btn = lv.button(screen)
        lv.label(self._cancel_btn).set_text("Cancel")
        self._cancel_btn.add_event_cb(lambda e: self.cancel_rename(), lv.EVENT.CLICKED, None)
        self._cancel_btn.align(lv.ALIGN.CENTER, 0, 80)
        self._cancel_btn.add_flag(lv.obj.FLAG.HIDDEN)

        self.setContentView(screen)

    def delete_cb(self):
        try:
            os.remove(self._path)
        except OSError:
            try:
                os.rmdir(self._path)
            except OSError as e:
                print(f"Error deleting {self._path}: {e}")
        self.finish()

    def show_rename_ui(self):
        self._delete_btn.add_flag(lv.obj.FLAG.HIDDEN)
        self._rename_btn.add_flag(lv.obj.FLAG.HIDDEN)
        self._rename_ta.remove_flag(lv.obj.FLAG.HIDDEN)
        self._confirm_btn.remove_flag(lv.obj.FLAG.HIDDEN)
        self._cancel_btn.remove_flag(lv.obj.FLAG.HIDDEN)

    def confirm_rename(self):
        dir_part = '/'.join(self._path.rstrip('/').split('/')[:-1]) or '/'
        new_name = self._rename_ta.get_text()
        new_path = f"{dir_part}/{new_name}"
        try:
            os.rename(self._path, new_path)
        except OSError as e:
            print(f"Error renaming {self._path} to {new_path}: {e}")
        self.finish()

    def cancel_rename(self):
        self._delete_btn.remove_flag(lv.obj.FLAG.HIDDEN)
        self._rename_btn.remove_flag(lv.obj.FLAG.HIDDEN)
        self._rename_ta.add_flag(lv.obj.FLAG.HIDDEN)
        self._confirm_btn.add_flag(lv.obj.FLAG.HIDDEN)
        self._cancel_btn.add_flag(lv.obj.FLAG.HIDDEN)
