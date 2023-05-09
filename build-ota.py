import os
import requests
import shutil
import subprocess
from tqdm import tqdm

AVBKEY = "./keys/avb.key"
OTAKEY = "./keys/ota.key"
AVB_PKMD= "./keys/avb_pkmd.bin"
OTACERT = "./keys/ota.crt"
PROGESS= False

root_dir = "./factory_ota"
allowed_buildtypes = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]


"""
The provided code contains three functions: `print_root_dir`, `print_type_dir`, and `version_dir`. These functions are related to navigating a directory structure and printing out its contents. 

The `print_root_dir` function prints out the available build types in the root directory. The `print_type_dir` function prints out the available devices for a given build type. The `version_dir` function constructs a path to a version directory and prints out its contents in a tree structure if it exists.
"""

def print_root_dir() -> None:
    """
    Prints the content of the root directory, including a list of available build types.
    """
    global root_dir  # assuming root_dir is a global variable
    print(f"Available build types in {root_dir}:")
    for d in allowed_buildtypes:  # assuming allowed_buildtypes is a global variable
        print(f"- {d}")

def print_type_dir(buildtype: str) -> None:
    """
    Prints the content of the directory for the given build type, including a list of available devices.
    
    :param buildtype: The build type to search for.
    """
    global root_dir  # assuming root_dir is a global variable
    type_dir = os.path.join(root_dir, buildtype)
    if os.path.exists(type_dir):
        print(f"Available devices for {buildtype}:")
        for subdir in os.listdir(type_dir):
            if os.path.isdir(os.path.join(type_dir, subdir)):
                print(f"- {subdir}")
    else:
        print(f"No directory found for build type {buildtype}")

def version_dir(buildtype: str, device: str) -> None:
    """
    Constructs the version directory path and checks if it exists. If it does, prints the subdirectories as a tree structure.
    
    :param buildtype: The build type to search for.
    :param device: The device to search for.
    """
    global root_dir  # assuming root_dir is a global variable
    version_dir = os.path.join(root_dir, buildtype, device)
    if os.path.exists(version_dir):
        print(f"Version directory found: {version_dir}")
        # Print the subdirectories as a tree structure
        for root, dirs, files in os.walk(version_dir):
            level = root.replace(version_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                print(f"{sub_indent}{file}")
    else:
        print(f"No directory found for {device} for build type {buildtype}")

# Function to print the current selection

def print_selection(buildtype, device, version, id, magisk):
    print(" ")
    print("#" * 50)
    print("  ")
    print(f"BUILDTYPE : {buildtype}")
    print(f"DEVICE : {device}")
    print(f"VERSION: {version}")
    print(f"ID: {id}")
    print(f"MAGISK: {magisk}")
    print(" ")
    print("#" * 50)
    print("  ")



"""
This code defines a function named `generate_keys()`. The function performs several tasks related to 
generating encryption keys and certificates for Android Verified Boot (AVB) and Over-The-Air (OTA) updates.

The code first checks whether the AVB key file (`AVBKEY`) exists in the file system. If it does not exist,
the function generates a new RSA private key using the `openssl` command-line tool with a key size of 4096 bits. 
The generated key is then converted to the PKCS#8 format and encrypted with a scrypt-based passphrase. 
The encrypted key is saved in the `AVBKEY` file. If the `AVB_PKMD` file exists, it is removed.

Next, the code checks whether the `AVB_PKMD` file exists in the file system. If it does not exist, 
the function extracts the public key from the `AVBKEY` file using the `avbtool.py` script located in the `avbroot/external/avb/` directory. 
The extracted public key is saved in the `AVB_PKMD` file.

Then, the code checks whether the OTA key file (`OTAKEY`) exists in the file system.
If it does not exist, the function generates a new RSA private key using the `openssl` command-line tool with a key size of 4096 bits. 
The generated key is then converted to the PKCS#8 format and encrypted with a scrypt-based passphrase. The encrypted key is saved in the `OTAKEY` file. 
If the `OTACERT` file exists, it is removed.

Finally, the code checks whether the `OTACERT` file exists in the file system. 
If it does not exist, the function generates a new self-signed X.509 certificate using the `openssl` command-line tool. 
The certificate is signed using the private key stored in the `OTAKEY` file and has a validity period of 10000 days. 
The generated certificate is saved in the `OTACERT` file.
"""

def generate_keys():
    if not os.path.exists(AVBKEY):
        print(f"{AVBKEY} does not exist.")
        subprocess.run(["openssl", "genrsa", "4096", "|", "openssl", "pkcs8", "-topk8", "-scrypt", "-out", AVBKEY], shell=True)
        if os.path.exists(AVBKEY):
            os.remove(AVB_PKMD)

    if not os.path.exists(AVB_PKMD):
        print(f"{AVB_PKMD} does not exist.")
        subprocess.run(["python", "./avbroot/external/avb/avbtool.py", "extract_public_key", "--key", AVBKEY, "--output", AVB_PKMD])

    if not os.path.exists(OTAKEY):
        print(f"{OTAKEY} does not exist.")
        subprocess.run(["openssl", "genrsa", "4096", "|", "openssl", "pkcs8", "-topk8", "-scrypt", "-out", OTAKEY], shell=True)
        if os.path.exists(OTACERT):
            os.remove(OTACERT)

    if not os.path.exists(OTACERT):
        print(f"{OTACERT} does not exist.")
        subprocess.run(["openssl", "req", "-new", "-x509", "-sha256", "-key", OTAKEY, "-out", OTACERT, "-days", "10000", "-subj", "/CN=OTA/"])

    select_build_type()

"""
These are three functions related to modifying OTA updates for an Android device. 

The `extract_boot_image()` function extracts the boot image from an OTA update file and places it in a directory, 
with an option to also apply Magisk to the boot image.

The `patch_preinit_ota()` function patches the original OTA update file with Magisk and creates a new OTA update file that can be flashed on the device. 
It takes additional parameters for the device partition to patch and the Magisk version to use.

The `patch_ota()` function is similar to `patch_preinit_ota()`, but it doesn't patch the device partition and instead patches the entire OTA update file, 
including the boot image. It also takes a Magisk version parameter. 

All three functions rely on `avbroot.py`, which is a Python script that handles AVB (Android Verified Boot) functionality for modifying the OTA updates. 
The `AVBKEY`, `OTAKEY`, and `OTACERT` variables are paths to cryptographic keys and certificates used for signing and verifying the OTA updates.
"""

def extract_boot_image(buildtype, device, version, id):
    os.system('cls' if os.name == 'nt' else 'clear')
    print_selection(buildtype, device, version, id, " ")    
    subprocess.run(["python", 
                    "./avbroot/avbroot.py", "extract",
                    "--input", f"./factory_ota/{buildtype}/{device}/{version}/{id}.zip", 
                    "--directory", f"./factory_ota/{buildtype}/{device}/{version}/boot/{id}/", 
                    "--boot-only"])
    select_magisk()


def patch_preinit_ota(buildtype, device, version, id, magisk, partition):
    subprocess.run(["python", 
                    "./avbroot/avbroot.py", "patch", 
                    "--input", f"./factory_ota/{buildtype}/{device}/{version}/{id}.zip", 
                    "--privkey-avb", AVBKEY, 
                    "--privkey-ota", OTAKEY, 
                    "--cert-ota", OTACERT, 
                    "--magisk-preinit-device", partition, 
                    "--magisk", f"./magisk/Magisk-v{magisk}.apk"])
    

def patch_ota(buildtype, device, version, id, magisk):
    subprocess.run(["python", 
                    "./avbroot/avbroot.py", "patch", 
                    "--input", f"./factory_ota/{buildtype}/{device}/{version}/{id}.zip", 
                    "--privkey-avb", AVBKEY, 
                    "--privkey-ota", OTAKEY, 
                    "--cert-ota", OTACERT, 
                    "--magisk", f"./magisk/Magisk-v{magisk}.apk"])
    

"""
The select_build_type() function is used to prompt the user to select the build type (AOSP, Pixel, or Graphene) and call the select_device() function with the selected build type if the input is valid, otherwise it calls itself again.

The select_device() function prompts the user to select the device and calls the select_build_version() function with the selected build type and device if the input is valid, otherwise it calls itself again.

The select_magisk() function prompts the user to enter the Magisk version and calls the appropriate patch function based on the version selected.

The check_ota_exists() function checks if the OTA file exists for the given build type, device, version, and id.

The check_bootimage_exists() function checks if the boot image files exist for the given build type, device, version, and id.

In summary, these functions provide a simple command-line interface to download and patch OTA updates for Android devices.
"""

def select_build_type():
    os.system('cls' if os.name == 'nt' else 'clear')
    # Call print_selection to print the current selection
    print_selection("", "", "", "", "")
    # Call print_root_dir to print the root directory
    print_root_dir()
    # Define the available build types
    buildtypes = ["aosp", "pixel", "graphene", "download_ota"]
    # Prompt the user to select the build type
    buildtype = input("Please enter the buildtype(aosp, pixel, graphene): ")
    # If the build type is valid, call select_device
    if buildtype in buildtypes:
        select_device(buildtype)
    # Otherwise, call select_build_type again
    else:
        select_build_type()


def select_device(buildtype):
    os.system('cls' if os.name == 'nt' else 'clear')
    # Call print_selection to print the current selection
    print_selection(buildtype, "", "", "", "")
    # Call print_type_dir to print the available devices for the selected build type
    print_type_dir(buildtype)
    # Define the available devices
    devices = ["cheetah", "panther", "bluejay", "raven", "oriole", "barbet", "redfin", "bramble", "sunfish", "coral", "flame"]
    # Prompt the user to select the device
    device = input("Please enter the device(cheetah, raven, ...): ")
    # If the device is valid, call select_build_version
    if device in devices:
        select_build_version(buildtype, device)
    # Otherwise, call select_device again
    else:
        select_device(buildtype)


def select_magisk(buildtype, device, version, id):
    magisk = input("Please enter the magisk version (25.2, 26.1, ...): ")
    if float(magisk) > 25.2:
        partition = "persist"
        patch_preinit_ota(buildtype, device, version, id, magisk, partition)
    else:
        patch_ota(buildtype, device, version, id, magisk)



# Function to check if the OTA file exists
def check_ota_exists(buildtype, device, version, id):
    filepath = f"./factory_ota/{buildtype}/{device}/{version}/{id}.zip"
    return os.path.exists(filepath)


# Function to check if the boot image files exist
def check_bootimage_exists(buildtype, device, version, id):
    bootimage = f"./factory_ota/{buildtype}/{device}/{version}/{id}/boot.img"
    init_bootimage = f"./factory_ota/{buildtype}/{device}/{version}/{id}/init_boot.img"
    return os.path.exists(bootimage) and os.path.exists(init_bootimage)

"""
This script defines two functions: `select_build_version` and `check_url`.

`select_build_version` takes two arguments, `buildtype` and `device`. 
The function prints out the current selection based on the given buildtype and device, calls the `version_dir` function,
and prompts the user to enter a build-number. It then splits the build number into two parts: the version and the ID. 
It checks if an OTA update exists for the given buildtype, device, version, and ID. If it exists, 
it sets the `ota_filepath` variable to the path of the OTA update file. If the boot image for this version has already been extracted, 
it prints out a message saying so. Otherwise, it calls the `extract_boot_image` function to extract the boot image from the OTA update. 
If an OTA update does not exist for the given buildtype, device, version, and ID, it calls the `download_ota` function.

`check_url` takes a single argument, `url`. The function checks if the URL contains `dl.google.com` or `releases.grapheneos.org` 
and returns `"google"` or `"grapheneos"`, respectively. If the URL does not contain either of these substrings, it returns `None`.

The `download_ota` function takes four arguments: `buildtype`, `device`, `version`, and `id`. 
It creates a path to the OTA update directory, clears the console, and prints the current selection based on the given buildtype, device, version, and ID. 
It prompts the user to enter the OTA update URL from the website and checks if it is a valid URL using the `check_url` function. 
If the URL is invalid, it prints a message and returns. Otherwise, it creates the OTA update directory if it does not exist, 
downloads the file using the `requests` library, and displays a progress bar using the `tqdm` library. 
It then copies the downloaded file to a file named `id.zip` in the OTA update directory and extracts the boot image using the `extract_boot_image` function.
"""


def select_build_version(buildtype, device):
    print_selection(buildtype, device, "", "", "")
    version_dir(buildtype, device)
    build = input("Please enter the build-number(TQ2A.230505.002.2023050500, ...): ")
    version, id = build.split('.', 1)
    uversion = version.upper()
    if check_ota_exists(buildtype, device, uversion, id):
        ota_filepath = os.path.join("./factory_ota", buildtype, device, uversion, f"{id}.zip")
        if check_bootimage_exists(buildtype, device, uversion, id):
            print("Boot image already extracted.")
        else:
            extract_boot_image(buildtype, device, uversion, id)
    else: 
        print_selection(buildtype, device, uversion, id,"")
        download_ota(buildtype, device, uversion, id)



def check_url(url):
    if "dl.google.com" in url:
        return "google"
    elif "releases.grapheneos.org" in url:
        return "grapheneos"
    else:
        return None


def download_ota(buildtype, device, version, id):
    otapath = f"./factory_ota/{buildtype}/{device}/{version}/"
    os.system('cls' if os.name == 'nt' else 'clear')
    print_selection(buildtype, device, version, id,"")
    # Check if the URL is valid
    url = input("Please enter the OTA URL from the website: ")
    os.system('cls' if os.name == 'nt' else 'clear')
    print_selection(buildtype, device, version, id,"")
    url_type = check_url(url)
    if url_type is None:
        print("Invalid URL. Please provide a valid OTA update URL from the website.")
        return

    os.makedirs(otapath, exist_ok=True)

    # Download the file
    response = requests.get(url, stream=True)
    filename = os.path.join(otapath, os.path.basename(url))
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    with open(filename, "wb") as f, tqdm(total=total_size, unit='iB', unit_scale=True) as progress_bar:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            f.write(data)

    destination = f"{otapath}{id}.zip"
    if not os.path.exists(destination):
        print(destination)
        shutil.copyfile(filename, destination)

    print(f"OTA update downloaded and moved 1to {destination}")
    extract_boot_image()




generate_keys()
