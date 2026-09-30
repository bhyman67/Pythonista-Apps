"""Sync Pythonista app scripts from the current device's repository folder."""

import os
import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

import console
from objc_util import ObjCClass


GITHUB_REPOSITORY = 'bhyman67/Pythonista-Apps'
BRANCH = 'master'
RAW_BASE_URL = f'https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/{BRANCH}'
GITHUB_CONTENTS_URL = (
    f'https://api.github.com/repos/{GITHUB_REPOSITORY}/contents'
)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def app_script_name(app_name):
    """Map an app folder name to its lowercase script filename."""
    return re.sub(r'\s+', '_', app_name.lower()) + '.py'


def device_folder():
    """Return the repository folder matching this iOS device's idiom."""
    idiom = ObjCClass('UIDevice').currentDevice().userInterfaceIdiom()
    if idiom == 0:
        return 'This iPhone'
    if idiom == 1:
        return 'This iPad'
    raise ValueError('This sync script supports iPhone and iPad only.')


def remote_app_folders(device):
    """List app directories for this device from the GitHub repository."""
    url = (
        GITHUB_CONTENTS_URL.rstrip('/')
        + '/'
        + quote(device, safe='')
        + '?ref='
        + quote(BRANCH, safe='')
    )
    request = Request(
        url,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'Pythonista-App-Sync',
        },
    )
    with urlopen(request, timeout=30) as response:
        entries = json.loads(response.read().decode('utf-8'))
    return sorted(
        (
            entry['name'] for entry in entries
            if entry.get('type') == 'dir'
            and not entry.get('name', '').startswith('.')
        ),
        key=str.casefold,
    )


def sync_app(root, app_name, device):
    """Download and atomically replace one app's .py file; return any error."""
    script_name = app_script_name(app_name)
    app_dir = os.path.join(root, app_name)
    target_path = os.path.join(app_dir, script_name)
    temp_path = target_path + '.download'
    created_app_dir = False
    script_url = (
        RAW_BASE_URL.rstrip('/')
        + '/'
        + quote(device, safe='')
        + '/'
        + quote(app_name, safe='')
        + '/'
        + quote(script_name, safe='')
    )

    try:
        request = Request(
            script_url,
            headers={'User-Agent': 'Pythonista-App-Sync'},
        )
        with urlopen(request, timeout=30) as response:
            source = response.read()

        decoded_source = source.decode('utf-8')
        if not decoded_source.strip() or '<html' in decoded_source[:500].lower():
            raise ValueError('The URL did not return a Python source file.')
        compile(decoded_source, script_name, 'exec')

        if not os.path.isdir(app_dir):
            os.makedirs(app_dir)
            created_app_dir = True
        with open(temp_path, 'wb') as downloaded_file:
            downloaded_file.write(source)
        os.replace(temp_path, target_path)
        return None
    except Exception as error:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        if created_app_dir:
            try:
                os.rmdir(app_dir)
            except OSError:
                pass
        return str(error)


def main():
    if not RAW_BASE_URL.startswith('https://'):
        console.alert(
            'Invalid URL',
            'RAW_BASE_URL must use HTTPS.',
            'OK',
            hide_cancel_button=True,
        )
        return

    try:
        device = device_folder()
    except Exception as error:
        console.alert('Device Detection Failed', str(error), 'OK',
                      hide_cancel_button=True)
        return

    root = SCRIPT_DIR
    try:
        apps = remote_app_folders(device)
    except Exception as error:
        console.alert('Unable to Read Apps', str(error), 'OK',
                      hide_cancel_button=True)
        return

    if not apps:
        console.alert('No Apps Found', f'No app folders found in {root}.', 'OK',
                      hide_cancel_button=True)
        return

    choice = console.alert(
        f'Sync {device} Apps?',
        f'Create any missing folders and sync .py scripts for '
        f'{len(apps)} apps on this device? App data and other files '
        'will stay unchanged.',
        'Sync',
        'Cancel',
    )
    if choice != 1:
        return

    failures = []
    for app_name in apps:
        error = sync_app(root, app_name, device)
        if error:
            failures.append((app_name, error))

    synced = len(apps) - len(failures)
    if failures:
        details = '\n'.join(
            f'{name}: {error}' for name, error in failures[:8]
        )
        if len(failures) > 8:
            details += f'\nAnd {len(failures) - 8} more failure(s).'
        message = f'Synced {synced} of {len(apps)} apps.\n\n{details}'
        console.alert('Sync Finished with Errors', message, 'OK',
                      hide_cancel_button=True)
    else:
        console.alert('Sync Complete', f'Synced {synced} app scripts.', 'OK',
                      hide_cancel_button=True)


if __name__ == '__main__':
    main()