"""Download a Pythonista app script into its This iPhone folder."""

import os
import re
import urllib.request

import console


# Set this to the raw GitHub folder URL containing lowercase app script files.
RAW_BASE_URL = (
    'https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/'
)


def main():
    app_name = console.input_alert(
        'Update Pythonista App',
        'App folder name in This iPhone:',
        'Zoleo_Counter',
        'Continue',
    ).strip()
    if not app_name:
        return
    # Accept one folder name only; the input must not choose a filesystem path.
    if not re.fullmatch(r'[A-Za-z0-9_ -]+', app_name):
        console.alert(
            'Invalid App Name',
            'Use a folder name with letters, numbers, spaces, underscores, or hyphens.',
            'OK',
            hide_cancel_button=True,
        )
        return

    if 'OWNER/REPOSITORY' in RAW_BASE_URL:
        console.alert(
            'Set GitHub Base URL',
            'Edit RAW_BASE_URL with the raw URL to your repository folder.',
            'OK',
            hide_cancel_button=True,
        )
        return

    if not RAW_BASE_URL.startswith('https://'):
        console.alert('Invalid URL', 'The base URL must use HTTPS.', 'OK',
                      hide_cancel_button=True)
        return

    script_stem = re.sub(r'\s+', '_', app_name.lower())
    script_name = script_stem + '.py'
    script_url = RAW_BASE_URL.rstrip('/') + '/' + script_name
    updater_dir = os.path.dirname(os.path.abspath(__file__))
    # In the repo, apps are under This iPhone; on-device, this script is in that root.
    repo_phone_dir = os.path.join(updater_dir, 'This iPhone')
    this_phone_dir = repo_phone_dir if os.path.isdir(repo_phone_dir) else updater_dir
    app_dir = os.path.join(this_phone_dir, app_name)
    target_path = os.path.join(app_dir, script_name)
    # Keep the partial download separate so failures leave the installed file intact.
    temp_path = target_path + '.download'

    choice = console.alert(
        f'Update {app_name}?',
        f'Download {script_name} into {app_name}? Other files, including app data, stay unchanged.',
        'Update',
        'Cancel',
    )
    if choice != 1:
        return

    try:
        request = urllib.request.Request(
            script_url,
            headers={'User-Agent': 'Pythonista-Zoleo-Updater'},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            source = response.read()

        decoded_source = source.decode('utf-8')
        if not decoded_source.strip() or '<html' in decoded_source[:500].lower():
            raise ValueError('The URL did not return a Python source file.')
        # Only replace the installed script after the response parses as Python.
        compile(decoded_source, script_name, 'exec')

        os.makedirs(app_dir, exist_ok=True)
        with open(temp_path, 'wb') as downloaded_file:
            downloaded_file.write(source)
        os.replace(temp_path, target_path)
    except Exception as error:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        console.alert('Update Failed', str(error), 'OK', hide_cancel_button=True)
        return

    console.alert('Updated', f'{app_name}/{script_name} is up to date.', 'OK',
                  hide_cancel_button=True)


if __name__ == '__main__':
    main()
