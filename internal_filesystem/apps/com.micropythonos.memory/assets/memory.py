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
    LIGHT_BLUE = lv.color_hex(0x5DADE2)
    ORANGE = lv.color_hex(0xF39C12)
    GREEN = lv.color_hex(0x27AE60)
    RED = lv.color_hex(0xE74C3C)

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
        self.total_points = 0
        self.container = None
        self.buttons = []
        self.labels = []
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
        reset_btn.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        reset_btn.add_event_cb(self.on_reset, lv.EVENT.CLICKED, None)

    def build_board(self):
        if self.container:
            self.container.delete()
        self.container = lv.obj(self.screen)
        self.container.set_size(lv.pct(100), DisplayMetrics.pct_of_height(75))
        self.container.align(lv.ALIGN.CENTER, 0, 0)
        self.container.set_flex_flow(lv.FLEX_FLOW.ROW_WRAP)
        self.container.set_style_pad_row(2, 0)
        self.container.set_style_pad_column(2, 0)
        self.container.set_style_radius(0, 0)

        self.buttons = []
        self.labels = []
        for idx in range(len(self.hidden)):
            btn = lv.button(self.container)
            btn.set_size(lv.pct(95 // self.COLS), lv.pct(95 // self.ROWS))
            label = lv.label(btn)
            if self.revealed[idx]:
                label.set_text(self.hidden[idx] + "!")
            elif self.shown[idx] != " ":
                label.set_text(self.shown[idx])
            else:
                label.set_text("")
            label.center()
            btn.add_event_cb(lambda e, i=idx: self.on_button(e, i), lv.EVENT.CLICKED, None)
            self._color_button(btn, idx)
            self.buttons.append(btn)
            self.labels.append(label)

    def _color_button(self, btn, idx):
        if self.revealed[idx]:
            color = self.GREEN
        elif self.shown[idx] != " " and self.first_idx != -1 and self.second_idx != -1:
            color = self.RED
        elif self.shown[idx] != " ":
            color = self.ORANGE
        else:
            color = self.LIGHT_BLUE
        btn.set_style_bg_color(color, lv.PART.MAIN)

    def _update_all_buttons(self):
        for idx, btn in enumerate(self.buttons):
            label = self.labels[idx]
            if self.revealed[idx]:
                label.set_text(self.hidden[idx] + "!")
            elif self.shown[idx] != " ":
                label.set_text(self.shown[idx])
            else:
                label.set_text("")
            self._color_button(btn, idx)

    def refresh_labels(self):
        self.level_label.set_text(f"Level: {self.level}")
        self.moves_label.set_text(f"Moves: {self.moves}")
        self.points_label.set_text(f"Points: {self.total_points}")

    def on_button(self, event, idx):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_ts) < 50:
            return
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
                self.total_points += 1
                self.revealed[self.first_idx] = True
                self.revealed[self.second_idx] = True
                self.shown[self.first_idx] = " "
                self.shown[self.second_idx] = " "
                self.first_idx = -1
                self.second_idx = -1
                if all(self.revealed):
                    self.on_win()
            self.refresh_labels()

        self._update_all_buttons()

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
        self.total_points = 0
        self.new_game()
        self.build_board()
        self.refresh_labels()

    def onDestroy(self, screen):
        if self._win_timer:
            lv.timer_del(self._win_timer)
            self._win_timer = None
        if self.container:
            self.container.delete()
            self.container = None
