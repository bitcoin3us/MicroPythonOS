from mpos import Activity, DisplayMetrics
import random
import time


def _shuffle(lst):
    for i in range(len(lst) - 1, 0, -1):
        j = random.randint(0, i)
        lst[i], lst[j] = lst[j], lst[i]


class Memory(Activity):
    ROWS = 4
    COLS = 4
    SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def onCreate(self):
        self.screen = lv.obj()
        self.win_label = None
        self._last_ts = 0
        self.init_game()
        self.create_ui()
        self.setContentView(self.screen)

    def init_game(self):
        num_cells = self.ROWS * self.COLS
        num_pairs = num_cells // 2
        symbols = self.SYMBOLS[:num_pairs] * 2
        _shuffle(symbols)
        self.hidden = symbols[:num_cells]
        self.revealed = [False] * num_cells
        self.shown = [" "] * num_cells
        self.first_idx = -1
        self.second_idx = -1
        self.moves = 0

    def _build_btnm_map(self):
        parts = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                idx = r * self.COLS + c
                if self.revealed[idx]:
                    parts.append(self.hidden[idx] + "!")
                elif self.shown[idx] != " ":
                    parts.append(self.shown[idx])
                else:
                    parts.append(" ")
            parts.append("\n")
        parts.pop()
        parts.append("")
        return parts

    def update_btnm_map(self):
        self.btnm.set_map(self._build_btnm_map())

    def create_ui(self):
        self.moves_label = lv.label(self.screen)
        self.moves_label.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.points_label = lv.label(self.screen)
        self.points_label.align(lv.ALIGN.TOP_LEFT, 10, 10)
        self.refresh_labels()

        self.btnm = lv.buttonmatrix(self.screen)
        self.update_btnm_map()
        self.btnm.set_size(lv.pct(100), DisplayMetrics.pct_of_height(75))
        self.btnm.align(lv.ALIGN.CENTER, 0, 0)
        self.btnm.add_event_cb(self.on_button, lv.EVENT.VALUE_CHANGED, None)

        reset_btn = lv.button(self.screen)
        reset_label = lv.label(reset_btn)
        reset_label.set_text("New Game")
        reset_btn.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        reset_btn.add_event_cb(self.on_reset, lv.EVENT.CLICKED, None)

    def refresh_labels(self):
        self.moves_label.set_text(f"Moves: {self.moves}")
        points = sum(1 for r in self.revealed if r) // 2
        self.points_label.set_text(f"Points: {points}")

    def on_button(self, event):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_ts) < 50:
            return
        btnm = event.get_target_obj()
        idx = btnm.get_selected_button()
        if idx < 0 or idx >= len(self.hidden):
            return
        if self.revealed[idx] or self.shown[idx] != " ":
            return

        if self.first_idx != -1 and self.second_idx != -1:
            self.shown[self.first_idx] = " "
            self.shown[self.second_idx] = " "
            self.first_idx = -1
            self.second_idx = -1

        if self.first_idx == -1:
            self._last_ts = now
            self.first_idx = idx
            self.shown[idx] = self.hidden[idx]
        elif self.second_idx == -1 and idx != self.first_idx:
            self._last_ts = now
            self.second_idx = idx
            self.shown[idx] = self.hidden[idx]
            self.moves += 1
            if self.hidden[self.first_idx] == self.hidden[self.second_idx]:
                self.revealed[self.first_idx] = True
                self.revealed[self.second_idx] = True
                self.shown[self.first_idx] = " "
                self.shown[self.second_idx] = " "
                self.first_idx = -1
                self.second_idx = -1
                if all(self.revealed):
                    self.on_win()
            self.refresh_labels()

        self.update_btnm_map()

    def on_win(self):
        self.win_label = lv.label(self.screen)
        self.win_label.set_text(f"You Win! ({self.moves} moves)")
        self.win_label.align(lv.ALIGN.CENTER, 0, -30)
        self.win_label.set_style_text_color(lv.color_hex(0x00ff00), lv.PART.MAIN)

    def on_reset(self, event):
        if self.win_label:
            self.win_label.delete()
            self.win_label = None
        self._last_ts = time.ticks_ms()
        self.init_game()
        self.update_btnm_map()
        self.refresh_labels()

    def onDestroy(self, screen):
        pass
