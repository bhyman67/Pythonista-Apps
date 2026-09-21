"""
console.py -- minimal emulation of Pythonista's `console` module.

Only `alert()` is implemented, with the same positional return convention as
Pythonista: returns 1 for the first (primary) button, 2 for the second.

On Pythonista itself this file is never loaded -- the app imports its own
built-in `console` module instead.
"""

import tkinter as tk


def alert(title, message='', button1='OK', button2=None, hide_cancel_button=False):
    """Show a modal alert. Returns 1 or 2, matching Pythonista's console.alert.

    With a single button and hide_cancel_button=False (the Pythonista default),
    a 'Cancel' button is added, returning 2 when pressed.
    """
    root = tk._default_root or tk.Tk()
    owns_root = tk._default_root is None
    if owns_root:
        root.withdraw()

    if button2 is None and not hide_cancel_button:
        button2 = 'Cancel'

    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(root)
    result = [0]

    frame = tk.Frame(dialog, padx=24, pady=16, bg='#2b2b2d')
    frame.pack(fill='both', expand=True)
    tk.Label(frame, text=title, font=('Segoe UI Semibold', 12),
             fg='white', bg='#2b2b2d').pack(pady=(0, 6))
    if message:
        tk.Label(frame, text=message, font=('Segoe UI', 10), fg='#d0d0d0',
                 bg='#2b2b2d', wraplength=320, justify='center').pack(pady=(0, 14))

    def choose(value):
        result[0] = value
        dialog.destroy()

    buttons = tk.Frame(frame, bg='#2b2b2d')
    buttons.pack()
    tk.Button(buttons, text=button1, width=12, relief='flat', bg='#0a84ff',
              fg='white', activebackground='#0a84ff', activeforeground='white',
              command=lambda: choose(1)).pack(side='left', padx=4)
    if button2:
        tk.Button(buttons, text=button2, width=12, relief='flat', bg='#3a3a3c',
                  fg='white', activebackground='#3a3a3c', activeforeground='white',
                  command=lambda: choose(2)).pack(side='left', padx=4)

    dialog.protocol('WM_DELETE_WINDOW', lambda: choose(2 if button2 else 1))
    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f'+{max(x, 0)}+{max(y, 0)}')
    dialog.deiconify()
    dialog.grab_set()
    root.wait_window(dialog)
    if owns_root:
        root.destroy()
    return result[0]


def input_alert(title, message='', input_text='', ok_button_title='OK'):
    """Show a modal alert with a text field, mirroring Pythonista's
    console.input_alert. Returns the entered text, or '' if cancelled."""
    root = tk._default_root or tk.Tk()
    owns_root = tk._default_root is None
    if owns_root:
        root.withdraw()

    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(root)
    result = ['']

    frame = tk.Frame(dialog, padx=24, pady=16, bg='#2b2b2d')
    frame.pack(fill='both', expand=True)
    tk.Label(frame, text=title, font=('Segoe UI Semibold', 12),
             fg='white', bg='#2b2b2d').pack(pady=(0, 6))
    if message:
        tk.Label(frame, text=message, font=('Segoe UI', 10), fg='#d0d0d0',
                 bg='#2b2b2d', wraplength=320, justify='center').pack(pady=(0, 10))

    entry = tk.Entry(frame, font=('Segoe UI', 11), width=30,
                     bg='#3a3a3c', fg='white', insertbackground='white',
                     relief='flat')
    entry.insert(0, input_text)
    entry.pack(pady=(0, 14))

    def choose(value):
        result[0] = value
        dialog.destroy()

    buttons = tk.Frame(frame, bg='#2b2b2d')
    buttons.pack()
    tk.Button(buttons, text=ok_button_title, width=12, relief='flat', bg='#0a84ff',
              fg='white', activebackground='#0a84ff', activeforeground='white',
              command=lambda: choose(entry.get())).pack(side='left', padx=4)
    tk.Button(buttons, text='Cancel', width=12, relief='flat', bg='#3a3a3c',
              fg='white', activebackground='#3a3a3c', activeforeground='white',
              command=lambda: choose('')).pack(side='left', padx=4)

    entry.bind('<Return>', lambda e: choose(entry.get()))
    dialog.protocol('WM_DELETE_WINDOW', lambda: choose(''))
    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f'+{max(x, 0)}+{max(y, 0)}')
    dialog.deiconify()
    entry.focus_set()
    dialog.grab_set()
    root.wait_window(dialog)
    if owns_root:
        root.destroy()
    return result[0]
