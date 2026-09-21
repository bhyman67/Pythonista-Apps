"""
Zoleo Satellite Usage
---------------------
Tracks satellite messages (per conversation thread) and weather checks
against your 50-per-billing-period plan. Messages + weather checks share
the same pool of 50.

Data is saved to a JSON file after every tap, so nothing is lost between runs.

Usage:
  - Tap "+1" on a thread row each time you send that person a satellite message.
  - Tap "+1" on the Weather row each time you check the weather.
  - "-1" undoes an accidental tap.
  - "+ Add Thread" creates a named conversation thread (e.g. 'Wife', 'Dad').
  - Long-press a thread name to delete that thread.
  - Tap the "Renews ..." line to set the day of month your plan renews.
  - When a new billing period starts, you're prompted to reset automatically.
  - "Reset" (with confirmation) zeroes everything at any time.
"""

import ui
import os
import json
import console
from datetime import date, timedelta

# --- Settings ---
MONTHLY_LIMIT = 50

# Store data in Pythonista's own documents folder (always writable).
# Writing next to the script fails if it was opened as an external file
# (e.g. from OneDrive), because iOS only grants access to that one file.
try:
    DOCS_DIR = os.path.expanduser('~/Documents')
    if not os.path.isdir(DOCS_DIR):
        raise OSError('Documents folder not found')
except Exception:
    DOCS_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(DOCS_DIR, 'zoleo_count.json')

# --- Colors ---
BG_COLOR = '#1c1c1e'
ROW_COLOR = '#2c2c2e'
BUTTON_GRAY = '#3a3a3c'
GREEN = '#30d158'
YELLOW = '#ffd60a'
RED = '#ff453a'
BLUE = '#0a84ff'
SUBTLE = '#aaaaaa'


def default_data():
    return {'weather': 0, 'threads': {}, 'billing_day': None, 'period_start': None}


def load_data():
    """Read saved data from disk. Migrates the old single-counter format."""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        if 'threads' not in data:
            # Old format: {'count': N} -- fold it into a single thread.
            old = int(data.get('count', 0))
            data = default_data()
            if old > 0:
                data['threads']['Satellite Messages'] = old
        data.setdefault('weather', 0)
        data.setdefault('threads', {})
    except Exception:
        data = default_data()
    if not data.get('billing_day'):
        # Until the user sets their real billing day, assume it renews today.
        data['billing_day'] = date.today().day
    if not data.get('period_start'):
        data['period_start'] = period_bounds(data['billing_day'])[0].isoformat()
    return data


def save_data(data):
    """Write current data to disk."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def _clamp_day(year, month, day):
    """Clamp a day-of-month to that month's actual length (e.g. 31 -> 30)."""
    if month == 12:
        first_of_next = date(year + 1, 1, 1)
    else:
        first_of_next = date(year, month + 1, 1)
    last_day = (first_of_next - timedelta(days=1)).day
    return min(day, last_day)


def period_bounds(billing_day, today=None):
    """Return (period_start, renewal_date) for the current billing period.

    The period runs from the billing day (inclusive) until the next
    billing day (exclusive).
    """
    today = today or date.today()
    day_this_month = _clamp_day(today.year, today.month, billing_day)
    if today.day >= day_this_month:
        start = date(today.year, today.month, day_this_month)
        y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    else:
        start_month, start_year = (12, today.year - 1) if today.month == 1 \
            else (today.month - 1, today.year)
        start = date(start_year, start_month,
                     _clamp_day(start_year, start_month, billing_day))
        y, m = today.year, today.month
    renew = date(y, m, _clamp_day(y, m, billing_day))
    return start, renew


def fmt_date(d):
    """Format a date like 'Oct 5' (cross-platform, no strftime day flags)."""
    return f'{d:%b} {d.day}'


class ThreadRow(ui.View):
    """One row in the list: name, per-thread count, +1 and -1 buttons."""

    ROW_H = 56
    PAD = 12
    BTN_W = 46

    def __init__(self, app, key, is_weather=False):
        self.app = app
        self.key = key
        self.is_weather = is_weather
        self.background_color = ROW_COLOR
        self.corner_radius = 10

        self.name_label = ui.Label(
            font=('<system>', 16),
            text_color='white',
            alignment=ui.ALIGN_LEFT,
        )
        self.add_subview(self.name_label)

        self.count_label = ui.Label(
            font=('<system-bold>', 16),
            text_color='white',
            alignment=ui.ALIGN_CENTER,
        )
        self.add_subview(self.count_label)

        self.minus_button = ui.Button(
            title='\u22121',
            font=('<system-bold>', 18),
            background_color=BUTTON_GRAY,
            tint_color='white',
            corner_radius=8,
        )
        self.minus_button.action = self.decrement
        self.add_subview(self.minus_button)

        self.plus_button = ui.Button(
            title='+1',
            font=('<system-bold>', 18),
            background_color=BLUE if is_weather else GREEN,
            tint_color='black',
            corner_radius=8,
        )
        self.plus_button.action = self.increment
        self.add_subview(self.plus_button)

        # Long-press the name to delete a thread (weather row can't be deleted)
        if not is_weather:
            try:
                self.name_label.user_interaction_enabled = True
                self.name_label.add_recognizer(
                    ui.LongPressRecognizer(self.delete_thread)
                )
            except Exception:
                pass  # Desktop shim may not support recognizers
        self.refresh()

    def get_count(self):
        if self.is_weather:
            return self.app.data['weather']
        return self.app.data['threads'].get(self.key, 0)

    def refresh(self):
        label = '\U0001F324 Weather Checks' if self.is_weather else self.key
        self.name_label.text = label
        self.count_label.text = str(self.get_count())

    def layout(self):
        w, h = self.width, self.height
        p = self.PAD
        bw = self.BTN_W
        y = (h - 34) / 2
        self.plus_button.frame = (w - p - bw, y, bw, 34)
        self.minus_button.frame = (w - p - 2 * bw - 8, y, bw, 34)
        self.count_label.frame = (w - p - 2 * bw - 48, y, 32, 34)
        name_w = w - p - 2 * bw - 48 - p * 2
        self.name_label.frame = (p, 0, max(name_w, 40), h)

    def increment(self, sender):
        if self.is_weather:
            self.app.data['weather'] += 1
        else:
            self.app.data['threads'][self.key] = \
                self.app.data['threads'].get(self.key, 0) + 1
        self.app.data_changed()

    def decrement(self, sender):
        if self.is_weather:
            if self.app.data['weather'] > 0:
                self.app.data['weather'] -= 1
        else:
            cur = self.app.data['threads'].get(self.key, 0)
            if cur > 0:
                self.app.data['threads'][self.key] = cur - 1
        self.app.data_changed()

    def delete_thread(self, recognizer=None):
        # Only fire on the recognizer's "began" state (or a direct call).
        state = getattr(recognizer, 'state', None)
        if state is not None and state != 1:
            return
        count = self.app.data['threads'].get(self.key, 0)
        choice = console.alert(
            'Delete Thread?',
            f'Remove "{self.key}"? This subtracts {count} from your total.',
            'Delete',
        )
        if choice == 1:
            del self.app.data['threads'][self.key]
            self.app.data_changed(rebuild=True)


class ZoleoCounter(ui.View):
    def __init__(self):
        self.data = load_data()
        self.check_period_rollover()
        self.background_color = BG_COLOR
        self.rows = []

        # Close button (top-left, below status bar)
        self.close_button = ui.Button(
            title='\u2715',
            font=('<system-bold>', 20),
            background_color=BUTTON_GRAY,
            tint_color='white',
            corner_radius=22,
        )
        self.close_button.action = self.close_view
        self.add_subview(self.close_button)

        # Title
        self.title_label = ui.Label(
            text='\U0001F6F0 Zoleo Satellite Usage',
            font=('<system-bold>', 20),
            text_color='white',
            alignment=ui.ALIGN_CENTER,
        )
        self.add_subview(self.title_label)

        # Big total readout, e.g. "14 / 50"
        self.total_label = ui.Label(
            font=('<system-bold>', 48),
            text_color='white',
            alignment=ui.ALIGN_CENTER,
        )
        self.add_subview(self.total_label)

        # Remaining subtitle
        self.remaining_label = ui.Label(
            font=('<system>', 14),
            text_color=SUBTLE,
            alignment=ui.ALIGN_CENTER,
        )
        self.add_subview(self.remaining_label)

        # Billing period line (tap to change your billing day)
        self.period_button = ui.Button(
            title='',
            font=('<system>', 13),
            background_color=BG_COLOR,
            tint_color=SUBTLE,
            corner_radius=8,
        )
        self.period_button.action = self.edit_billing_day
        self.add_subview(self.period_button)

        # Progress bar
        self.bar_bg = ui.View(background_color=BUTTON_GRAY)
        self.bar_bg.corner_radius = 6
        self.bar_fill = ui.View(background_color=GREEN)
        self.bar_fill.corner_radius = 6
        self.bar_bg.add_subview(self.bar_fill)
        self.add_subview(self.bar_bg)

        # Scrollable thread list
        self.list = ui.ScrollView()
        self.list.background_color = BG_COLOR
        self.add_subview(self.list)

        # Add thread button
        self.add_thread_button = ui.Button(
            title='+ Add Thread',
            font=('<system-bold>', 16),
            background_color=BUTTON_GRAY,
            tint_color=BLUE,
            corner_radius=10,
        )
        self.add_thread_button.action = self.add_thread
        self.add_subview(self.add_thread_button)

        # Reset button
        self.reset_button = ui.Button(
            title='Reset (new billing period)',
            font=('<system>', 15),
            background_color=BUTTON_GRAY,
            tint_color=RED,
            corner_radius=10,
        )
        self.reset_button.action = self.reset
        self.add_subview(self.reset_button)

        self.rebuild_rows()
        self.update_display()

    # --- Layout ---

    def layout(self):
        w, h = self.width, self.height
        pad = 16
        self.close_button.frame = (20, 64, 44, 44)
        self.title_label.frame = (0, 72, w, 28)
        self.total_label.frame = (0, 106, w, 60)
        self.remaining_label.frame = (0, 166, w, 18)
        self.period_button.frame = (pad, 188, w - pad * 2, 24)
        self.bar_bg.frame = (pad, 218, w - pad * 2, 10)

        list_top = 238
        bottom_h = 110
        list_h = max(h - list_top - bottom_h, 80)
        self.list.frame = (pad, list_top, w - pad * 2, list_h)
        self.add_thread_button.frame = (pad, h - 100, w - pad * 2, 42)
        self.reset_button.frame = (pad, h - 50, w - pad * 2, 40)

        self.layout_rows()
        self.update_bar()

    def layout_rows(self):
        w = self.list.width
        y = 0
        for row in self.rows:
            row.frame = (0, y, w, ThreadRow.ROW_H)
            y += ThreadRow.ROW_H + 8
        self.list.content_size = (w, max(y, 1))

    # --- Data / display ---

    def total(self):
        return self.data['weather'] + sum(self.data['threads'].values())

    def usage_color(self):
        ratio = self.total() / MONTHLY_LIMIT
        if ratio >= 1.0:
            return RED
        elif ratio >= 0.7:
            return YELLOW
        return GREEN

    def update_bar(self):
        ratio = min(self.total() / MONTHLY_LIMIT, 1.0)
        self.bar_fill.frame = (0, 0, self.bar_bg.width * ratio, self.bar_bg.height)
        self.bar_fill.background_color = self.usage_color()

    def update_display(self):
        t = self.total()
        self.total_label.text = f'{t} / {MONTHLY_LIMIT}'
        remaining = MONTHLY_LIMIT - t
        if remaining > 0:
            self.remaining_label.text = f'{remaining} messages / weather checks left'
        else:
            self.remaining_label.text = 'Limit reached!'
        self.total_label.text_color = self.usage_color()
        self.update_bar()

        _, renew = period_bounds(self.data['billing_day'])
        days_left = (renew - date.today()).days
        plural = 's' if days_left != 1 else ''
        self.period_button.title = (
            f'Renews {fmt_date(renew)} \u00b7 {days_left} day{plural} left '
            f'\u00b7 tap to edit'
        )
        for row in self.rows:
            row.refresh()

    def rebuild_rows(self):
        for row in self.rows:
            try:
                row.remove_from_superview()
            except Exception:
                pass
        self.rows = [ThreadRow(self, 'weather', is_weather=True)]
        for name in sorted(self.data['threads'].keys()):
            self.rows.append(ThreadRow(self, name))
        for row in self.rows:
            self.list.add_subview(row)
        self.layout_rows()

    def data_changed(self, rebuild=False):
        save_data(self.data)
        if rebuild:
            self.rebuild_rows()
        self.update_display()

    # --- Button actions ---

    def close_view(self, sender):
        self.close()

    def add_thread(self, sender):
        name = console.input_alert(
            'New Thread',
            'Who is this conversation with? (e.g. Wife, Dad, Guide)',
            '',
            'Add',
        )
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name in self.data['threads']:
            console.alert('Already Exists',
                          f'A thread named "{name}" already exists.',
                          'OK', hide_cancel_button=True)
            return
        self.data['threads'][name] = 0
        self.data_changed(rebuild=True)

    def check_period_rollover(self):
        """On launch, if the billing period rolled over, offer a reset."""
        start, _ = period_bounds(self.data['billing_day'])
        if self.data.get('period_start') == start.isoformat():
            return
        choice = console.alert(
            'New Billing Period',
            f'Your plan renewed on {fmt_date(start)}. Reset all counts?',
            'Reset',
        )
        if choice == 1:
            self.data['threads'] = {}
            self.data['weather'] = 0
        # Remember the current period either way, so we don't ask again.
        self.data['period_start'] = start.isoformat()
        save_data(self.data)

    def edit_billing_day(self, sender):
        text = console.input_alert(
            'Billing Day',
            'What day of the month does your Zoleo plan renew? (1-31)',
            str(self.data['billing_day']),
            'Save',
        )
        if not text:
            return
        try:
            day = int(text.strip())
            if not 1 <= day <= 31:
                raise ValueError
        except ValueError:
            console.alert('Invalid Day', 'Please enter a number from 1 to 31.',
                          'OK', hide_cancel_button=True)
            return
        self.data['billing_day'] = day
        self.data['period_start'] = period_bounds(day)[0].isoformat()
        save_data(self.data)
        self.update_display()

    def reset(self, sender):
        choice = console.alert(
            'Reset Counter?',
            'Start a new billing period? This zeroes all threads and weather checks.',
            'Reset',
        )
        if choice == 1:
            billing_day = self.data['billing_day']
            self.data = default_data()
            self.data['billing_day'] = billing_day
            self.data['period_start'] = period_bounds(billing_day)[0].isoformat()
            save_data(self.data)
            self.rebuild_rows()
            self.update_display()


v = ZoleoCounter()
v.present('fullscreen', hide_title_bar=True)
