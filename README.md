# Pythonista App Inventory

This repository is a simple inventory of Pythonista apps used on an iPhone and iPad. It keeps each device's app folders together without turning every small app into a separate project.

## Folder Layout

`This iPhone/` and `This iPad/` represent the corresponding locations in Pythonista's file browser. Each app gets its own folder beneath the device folder. For example:

```text
This iPhone/
  Zoleo_Counter/
    zoleo_counter.py
    zoleo_count.json
    screenshots/
This iPad/
  .gitkeep
```

Keep each app folder intentionally small: it should contain exactly one `.py` file for the Pythonista app, plus that app's data files (such as JSON), images, screenshots, and other supporting assets. The JSON files are tracked in Git so people can see how the apps store their data. Do not put secrets or private information in tracked files.

An app folder belongs under the device where that app is installed. The iPad folder can remain empty until an app is added there.

## Desktop Testing

The root-level `ui.py` and `console.py` files are partial Tkinter shims for testing Pythonista scripts on desktop Python. Pythonista uses its own built-in `ui` and `console` modules instead. From the repository root, run the Zoleo counter on Windows with:

```powershell
\.venv\Scripts\python.exe "This iPhone\Zoleo_Counter\zoleo_counter.py"
```

The shims provide only the Pythonista APIs currently needed by the app; desktop behavior may not match every iOS interaction exactly.

## Updating on a Device

`sync_pythonista_apps.py` discovers app folders in the matching GitHub device folder. Copy it to the root of Pythonista's `This iPhone` or `This iPad` folder. It detects the device through UIKit, creates missing app folders after a successful script download, and maps each folder to a lowercase script filename, so `Zoleo_Counter` maps to `zoleo_counter.py`.

The script downloads each app's `.py` file from the matching device folder, validates the source, then replaces that script. JSON data, screenshots, and other assets are never downloaded or changed. Failed downloads are reported after the other apps have been attempted. Update `GITHUB_REPOSITORY` or `BRANCH` if the repository or branch changes. This updater runs in Pythonista and uses its `objc_util` module for device detection and the GitHub Contents API for app discovery.