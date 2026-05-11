from mpos import Activity, DisplayMetrics
import random


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
        self.timer = None
        self.win_label = None
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
        self.selected = []
        self.locked = False
        self.moves = 0

    def create_ui(self):
        title = lv.label(self.screen)
        title.set_text("Memory")
        title.align(lv.ALIGN.TOP_MID, 0, 10)

        self.moves_label = lv.label(self.screen)
        self.update_moves_label()
        self.moves_label.align(lv.ALIGN.TOP_MID, 0, 30)

        self.btnm = lv.buttonmatrix(self.screen)
        self.update_btnm_map()
        self.btnm.set_size(lv.pct(100), DisplayMetrics.pct_of_height(65))
        self.btnm.align(lv.ALIGN.CENTER, 0, 10)
        self.btnm.add_event_cb(self.on_button, lv.EVENT.VALUE_CHANGED, None)

        reset_btn = lv.button(self.screen)
        reset_label = lv.label(reset_btn)
        reset_label.set_text("New Game")
        reset_btn.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        reset_btn.add_event_cb(self.on_reset, lv.EVENT.CLICKED, None)

    def update_moves_label(self):
        self.moves_label.set_text(f"Moves: {self.moves}")

    def update_btnm_map(self):
        parts = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                idx = r * self.COLS + c
                if self.revealed[idx]:
                    parts.append(self.hidden[idx])
                elif self.shown[idx] != " ":
                    parts.append(self.shown[idx])
                else:
                    parts.append(" ")
            parts.append("\n")
        parts.pop()
        parts.append("")
        self.btnm.set_map(parts)

    def on_button(self, event):
        if self.locked:
            return
        btnm = event.get_target_obj()
        idx = btnm.get_selected_button()
        if idx < 0 or idx >= len(self.hidden):
            return
        if self.revealed[idx] or self.shown[idx] != " ":
            return

        self.shown[idx] = self.hidden[idx]
        self.selected.append(idx)
        self.update_btnm_map()

        if len(self.selected) == 2:
            self.moves += 1
            self.update_moves_label()
            self.locked = True
            first, second = self.selected
            if self.hidden[first] == self.hidden[second]:
                self.revealed[first] = True
                self.revealed[second] = True
                self.shown[first] = " "
                self.shown[second] = " "
                self.selected = []
                self.locked = False
                self.update_btnm_map()
                if all(self.revealed):
                    self.on_win()
            else:
                self.timer = lv.timer_create(self.on_hide_timeout, 3000, None)

    def on_hide_timeout(self, timer):
        self.timer = None
        for idx in self.selected:
            self.shown[idx] = " "
        self.selected = []
        self.locked = False
        self.update_btnm_map()

    def on_win(self):
        self.win_label = lv.label(self.screen)
        self.win_label.set_text(f"You Win! ({self.moves} moves)")
        self.win_label.align(lv.ALIGN.CENTER, 0, -30)
        self.win_label.set_style_text_color(lv.color_hex(0x00ff00), lv.PART.MAIN)

    def on_reset(self, event):
        if self.timer:
            self.timer.delete()
            self.timer = None
        if self.win_label:
            self.win_label.delete()
            self.win_label = None
        self.init_game()
        self.update_btnm_map()
        self.update_moves_label()

    def onDestroy(self, screen):
        if self.timer:
            self.timer.delete()
            self.timer = None
