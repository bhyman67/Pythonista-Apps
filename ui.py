"""
ui.py -- Tkinter-based emulation of Pythonista's `ui` module.

Implements just enough of the Pythonista API for scripts written against
`ui.View`, `ui.Label`, and `ui.Button` (with absolute `frame` positioning and
a `present()` call) to run on desktop Python. Rounded corners are drawn on an
internal Canvas since Tkinter has no native corner radius.

On Pythonista itself this file is never loaded -- the app imports its own
built-in `ui` module instead -- so the same script runs in both places.
"""

import tkinter as tk

# --- Alignment constants (values match Pythonista) ---
ALIGN_LEFT = 1
ALIGN_CENTER = 2
ALIGN_RIGHT = 3

_ALIGN_ANCHOR = {ALIGN_LEFT: 'w', ALIGN_CENTER: 'center', ALIGN_RIGHT: 'e'}

# Fonts that approximate Pythonista's named iOS fonts on Windows/macOS/Linux.
_FONT_MAP = [
    ('<system-bold>', 'Segoe UI Semibold'),
    ('<system>', 'Segoe UI'),
    ('<menlo>', 'Consolas'),
]


def _convert_font(font):
    """Translate a Pythonista (name, size) font tuple into a Tk font tuple."""
    if not isinstance(font, tuple) or len(font) != 2:
        return font
    name, size = font
    if size <= 0:
        size = 14
    for placeholder, fallback in _FONT_MAP:
        if name == placeholder:
            return (fallback, int(size))
    return (name, int(size))


def _get_root():
    root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()
    return root


class View:
    """Pythonista ui.View -- a container with absolute (x, y, w, h) frames.

    Setup happens in __new__ (as in Pythonista, where the native view is
    created before __init__), so subclasses like this script's ZoleoCounter
    work even when they never call super().__init__().
    """

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        root = _get_root()
        self._canvas = tk.Canvas(root, highlightthickness=0, bd=0)
        self._frame = (0, 0, 0, 0)
        self._superview = None
        self._presented_window = None
        self._corner_radius = 0
        self._bg = '#ffffff'
        self._canvas.configure(bg=self._bg)
        self._canvas.bind('<Configure>', self._on_configure)
        return self

    def __init__(self, background_color='#ffffff', corner_radius=0):
        self.corner_radius = corner_radius
        self.background_color = background_color

    # --- Tree structure ---

    def add_subview(self, subview):
        subview._superview = self
        if getattr(subview, '_transparent', False):
            subview._sync_bg()
        subview._place()

    # --- Geometry ---

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, value):
        self._frame = tuple(float(v) for v in value)
        self._place()

    @property
    def width(self):
        return self._frame[2]

    @property
    def height(self):
        return self._frame[3]

    def _place(self):
        x, y, w, h = self._frame
        if self._superview is not None:
            self._canvas.place(in_=self._superview._canvas, x=x, y=y,
                               width=max(w, 0), height=max(h, 0))
        self._redraw()

    def _on_configure(self, event):
        if self._superview is None:
            self._frame = (0, 0, event.width, event.height)
        self._redraw()
        layout = getattr(self, 'layout', None)
        if callable(layout) and not isinstance(self, (Label, Button)):
            layout()

    # --- Appearance ---

    @property
    def background_color(self):
        return self._bg

    @background_color.setter
    def background_color(self, color):
        self._bg = color
        self._canvas.configure(bg=color)
        self._redraw()

    def _redraw(self):
        canvas = self._canvas
        tag = '_bgfill'
        canvas.delete(tag)
        w, h = self._frame[2], self._frame[3]
        radius = getattr(self, 'corner_radius', 0) or 0
        if w <= 0 or h <= 0:
            return
        if radius > 0:
            r = min(radius, w / 2, h / 2)
            points = [r, 0, w - r, 0, w, 0, w, r, w, h - r, w, h, w - r, h,
                      r, h, 0, h, 0, h - r, 0, r, 0, 0]
            canvas.create_polygon(points, smooth=True, fill=self._bg,
                                  outline=self._bg, tags=tag)
            canvas.tag_lower(tag)

    # --- Presentation ---

    def present(self, style='default', hide_title_bar=False):
        root = _get_root()
        if self._superview is not None:
            return
        self._presented_window = root
        root.deiconify()
        root.title(getattr(self, 'name', '') or 'Pythonista Script')
        root.configure(bg=self._bg)
        root.geometry('400x560')
        if style in ('fullscreen', 'full_screen'):
            try:
                root.attributes('-fullscreen', True)
                root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))
            except tk.TclError:
                root.state('zoomed')
        self._canvas.pack(fill='both', expand=True)
        self._frame = (0, 0, max(root.winfo_width(), 1),
                       max(root.winfo_height(), 1))
        root.mainloop()

    def close(self):
        """Close the presented window (mirrors Pythonista's View.close())."""
        window = self._presented_window
        if window is not None:
            self._presented_window = None
            window.destroy()
        else:
            # Not presented via present(); just detach from the superview.
            self._canvas.place_forget()
            self._superview = None

    def remove_from_superview(self):
        """Detach this view from its parent (mirrors Pythonista's API)."""
        self._canvas.place_forget()
        self._superview = None

    def bring_subview_to_front(self, subview):
        """Raise a subview above its siblings."""
        try:
            subview._canvas.lift()
        except Exception:
            pass


class ScrollView(View):
    """Pythonista ui.ScrollView -- vertical scrolling container.

    Desktop approximation: a fixed-height canvas that clips its children.
    (No mouse-wheel scrolling; keep content short when testing on desktop.)
    """

    def __init__(self, background_color='#ffffff'):
        super().__init__(background_color=background_color)
        self._content_size = (0, 0)

    @property
    def content_size(self):
        return self._content_size

    @content_size.setter
    def content_size(self, value):
        self._content_size = tuple(value)


class Label(View):
    """Pythonista ui.Label -- static text on a transparent background."""

    def __init__(self, text='', font=('<system>', 14), text_color='#000000',
                 alignment=ALIGN_LEFT, background_color=None):
        super().__init__(background_color=background_color or '#ffffff')
        self._tk_label = tk.Label(
            self._canvas, text=text, font=_convert_font(font),
            fg=text_color, anchor=_ALIGN_ANCHOR.get(alignment, 'w'))
        self._tk_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._transparent = background_color is None
        if self._transparent:
            self._sync_bg()
        self._text = text

    def _sync_bg(self):
        parent_bg = getattr(self._superview, 'background_color', '#ffffff') \
            if self._superview else '#ffffff'
        self._tk_label.configure(bg=parent_bg)

    @View.background_color.setter
    def background_color(self, color):
        View.background_color.fset(self, color)
        if getattr(self, '_transparent', False):
            self._sync_bg()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self._tk_label.configure(text=value)

    @property
    def text_color(self):
        return self._tk_label.cget('fg')

    @text_color.setter
    def text_color(self, color):
        self._tk_label.configure(fg=color)


class Button(View):
    """Pythonista ui.Button -- tappable rounded rect with an action callback."""

    def __init__(self, title='', font=('<system>', 14),
                 background_color='#e0e0e0', tint_color='#000000',
                 corner_radius=8, action=None):
        super().__init__(background_color=background_color,
                         corner_radius=corner_radius)
        self._tk_button = tk.Button(
            self._canvas, text=title, font=_convert_font(font),
            fg=tint_color, activeforeground=tint_color,
            bg=background_color, activebackground=background_color,
            relief='flat', bd=0, highlightthickness=0,
            command=self._fire_action)
        self._tk_button.place(x=0, y=0, relwidth=1, relheight=1)
        self.action = action

    def _fire_action(self):
        if callable(self.action):
            self.action(self)

    @property
    def title(self):
        return self._tk_button.cget('text')

    @title.setter
    def title(self, value):
        self._tk_button.configure(text=value)

    @View.background_color.setter
    def background_color(self, color):
        View.background_color.fset(self, color)
        if hasattr(self, '_tk_button'):
            self._tk_button.configure(bg=color, activebackground=color)
