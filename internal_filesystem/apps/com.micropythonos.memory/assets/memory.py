from mpos import Activity, DisplayMetrics
import random
import time


def _shuffle(lst):
    for i in range(len(lst) - 1, 0, -1):
        j = random.randint(0, i)
        lst[i], lst[j] = lst[j], lst[i]


def _grid_dims(n):
    best = (1, n)
    for r in range(1, int(n**0.5) + 1):
        if n % r == 0:
            c = n // r
            if abs(r - c) < abs(best[0] - best[1]):
                best = (r, c)
    return best


class Memory(Activity):
    SYMBOLS = [
        chr(61441), chr(61448), chr(61451), chr(61452), chr(61452), chr(61453),
        chr(61457), chr(61459), chr(61461), chr(61465), chr(61468), chr(61473),
        chr(61478), chr(61479), chr(61480), chr(61502), chr(61507), chr(61512),
        chr(61515), chr(61516), chr(61517), chr(61521), chr(61522), chr(61523),
        chr(61524), chr(61543), chr(61544), chr(61550), chr(61552), chr(61553),
        chr(61556), chr(61559), chr(61560), chr(61561), chr(61563), chr(61587),
        chr(61589), chr(61636), chr(61637), chr(61639), chr(61641), chr(61664),
        chr(61671), chr(61674), chr(61683), chr(61724), chr(61732), chr(61787),
        chr(61931), chr(62016), chr(62017), chr(62018), chr(62019), chr(62020),
        chr(62087), chr(62099), chr(62212), chr(62189), chr(62810), chr(63426),
        chr(63650),
        chr(0xf002), chr(0xf004), chr(0xf005), chr(0xf00e), chr(0xf010),
        chr(0xf029), chr(0xf030),
        chr(0xf15a), chr(0xf164), chr(0xf165), chr(0xf1e0),
        chr(0xf2ea), chr(0xf379), chr(0xf58f),
        chr(0x2022), chr(0x20bf), chr(0x4e2f), chr(0x4e30),
    ]

    def onCreate(self):
        self.screen = lv.obj()
        self._last_ts = 0
        self._win_timer = None
        self.level = 1
        self.btnm = None
        self.new_game()
        self.create_ui()
        self.setContentView(self.screen)

    def new_game(self):
        num_cells = self.level * 2
        self.ROWS, self.COLS = _grid_dims(num_cells)
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
        self.level_label = lv.label(self.screen)
        self.level_label.align(lv.ALIGN.TOP_MID, 0, 10)

        self.moves_label = lv.label(self.screen)
        self.moves_label.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.points_label = lv.label(self.screen)
        self.points_label.align(lv.ALIGN.TOP_LEFT, 10, 10)
        self.refresh_labels()

        self.build_board()

        reset_btn = lv.button(self.screen)
        reset_label = lv.label(reset_btn)
        reset_label.set_text("New Game")
        reset_btn.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        reset_btn.add_event_cb(self.on_reset, lv.EVENT.CLICKED, None)

    def build_board(self):
        if self.btnm:
            self.btnm.delete()
        self.btnm = lv.buttonmatrix(self.screen)
        self.update_btnm_map()
        self.btnm.set_size(lv.pct(100), DisplayMetrics.pct_of_height(75))
        self.btnm.align(lv.ALIGN.CENTER, 0, 0)
        self.btnm.add_event_cb(self.on_button, lv.EVENT.VALUE_CHANGED, None)

    def refresh_labels(self):
        self.level_label.set_text(f"Level: {self.level}")
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
        self._win_timer = lv.timer_create(self._advance_level, 1000, None)
        self._win_timer.set_repeat_count(1)

    def _advance_level(self, timer):
        self._win_timer = None
        self.level += 1
        self._last_ts = time.ticks_ms()
        self.new_game()
        self.build_board()
        self.refresh_labels()

    def on_reset(self, event):
        if self._win_timer:
            lv.timer_del(self._win_timer)
            self._win_timer = None
        self._last_ts = time.ticks_ms()
        self.level = 1
        self.new_game()
        self.build_board()
        self.refresh_labels()

    def onDestroy(self, screen):
        if self._win_timer:
            lv.timer_del(self._win_timer)
            self._win_timer = None
