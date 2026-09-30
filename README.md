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

`update_pythonista_app.py` is a general-purpose updater. In the repository it is at the root; copy it to the root of Pythonista's `This iPhone` folder to run it on the device. Set `RAW_BASE_URL` in the script to the GitHub raw-content folder containing the app scripts.

The updater asks for the app folder name, then downloads only the corresponding `.py` file. For example, `Zoleo_Counter` maps to `zoleo_counter.py`. It does not download or replace JSON data, screenshots, or other assets, so those remain untouched by script updates.