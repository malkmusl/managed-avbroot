import os
import platform
import subprocess
import requests
import zipfile
import io
import sys
from tqdm import tqdm

def download_file(url, output_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        block_size = 1024
        t=tqdm(total=total_size, unit='iB', unit_scale=True)
        with open(output_path, 'wb') as f:
            for data in r.iter_content(block_size):
                t.update(len(data))
                f.write(data)
        t.close()

def download_and_extract_adb():
    system = platform.system()
    url = None
    if system == 'Windows':
        url = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'
    elif system == 'Linux':
        url = 'https://dl.google.com/android/repository/platform-tools-latest-linux.zip'
    elif system == 'Darwin':
        url = 'https://dl.google.com/android/repository/platform-tools-latest-darwin.zip'
    else:
        print('Error: Unsupported system.')
        return
    
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f'Error: Failed to download file. HTTP status code {r.status_code}.')
        return

    zip_file = zipfile.ZipFile(io.BytesIO(r.content))
    zip_file.extractall('./')

def add_to_path():
    current_path = os.environ.get('PATH', '')
    platform_tools_path = os.path.abspath('./platform-tools')
    if platform_tools_path not in current_path:
        if sys.platform.startswith('win'):
            subprocess.run(['setx', 'PATH', f'{current_path};{platform_tools_path}'], check=True)
        else:
            shell_config_files = ['.bashrc', '.bash_profile', '.zshrc']
            for config_file in shell_config_files:
                with open(os.path.expanduser(f'~/{config_file}'), 'a') as f:
                    f.write(f'\nexport PATH="{platform_tools_path}:$PATH"\n')
        os.chmod(platform_tools_path, 0o777)  # make directory executable
        for root, dirs, files in os.walk(platform_tools_path):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o777)  # make directories executable
            for f in files:
                os.chmod(os.path.join(root, f), 0o777)  # make files executable
    print(f'Added {platform_tools_path} to PATH environment variable.')



def check_adb_connection():
    # Check if adb is installed
    if os.system("adb version") != 0:
        print("ADB is not installed.")
        return False

    # Check if a device is connected
    output = os.popen("adb devices").read()
    if "device" not in output:
        print("No device found.")
        return False

    # Check if the device is authorized
    output = os.popen("adb shell getprop ro.product.model").read()
    if "device unauthorized" in output:
        print("Device is not authorized. Please check your device.")
        return False

    # Check if the device is in USB debugging mode
    output = os.popen("adb shell getprop sys.usb.state").read()
    if "debugging" not in output:
        print("Device is not in USB debugging mode. Please enable it.")
        return False

    print("ADB connection is OK.")
    return True


def get_device_name():
    try:
        output = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.product.model'])
        return output.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None


def get_device_if_connected():
    if check_adb_connection():
        return get_device_name()
    else:
        return None


def main():
    if os.system("adb version") != 0:
        print("ADB is not installed.")
        download_and_extract_adb()
        add_to_path()
    else:
        check_adb_connection()
        if get_device_if_connected() != 0:
            print(get_device_name)



if __name__ == '__main__':
    main()
