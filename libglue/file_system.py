"""File systems library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

import json
import os
import shutil
import string
import subprocess
import sys
import time
from importlib import resources
from pathlib import Path
from typing import Any

import psutil
import yaml
from rich.pretty import pprint
from rich.prompt import Confirm

from .console import banner, console, log
from .convert import convert
from .data import load_json, sort_dictionary
from .shell import shell
from .types import WriteFlags


def find_root(directory: Path, match: str = ".git"):
    """Determine root directory based on file name."""
    for path in Path(directory).parents:
        if Path(path / match).exists():
            return path
    return None


def get_cache_directory() -> Path:
    """Return cache directory."""
    if "XDG_CACHE_HOME" in os.environ:
        path = Path(os.environ["XDG_CACHE_HOME"])
        if path.exists():
            return path

    return Path.home() / ".cache"


def get_config_directory() -> Path:
    """Return config directory."""
    if "XDG_CONFIG_HOME" in os.environ:
        path = Path(os.environ["XDG_CONFIG_HOME"])
        if path.exists():
            return path

    return Path.home() / ".config"


def load_yaml_resource(resource_name: str, path: str):
    """Load YAML file as Python dictionary from Python resources."""
    with resources.open_binary(resource_name, path) as _fp:
        return yaml.safe_load(_fp)


def load_yaml_file(path: Path):
    """Read YAML file and return it as a python dictionary."""
    try:
        return yaml.safe_load(read_file(path))
    except ValueError as error:
        log.error("failed to read yaml file (%s)", error)
        raise SystemExit(1) from error


def get_directory_paths(directory: Path, type: str):
    """Return sorted list with paths, exit when directory does not exist."""
    if not directory.is_dir():
        console.log(f":person_facepalming: could not find {type} directory: {directory}")
        sys.exit(1)

    return sorted(directory.iterdir())


def load_yaml_directory(directory: Path, type: str):
    """Load and return directory with yaml files."""
    return [load_yaml_file(file) for file in get_directory_paths(directory, type)]


def load_yaml_directory_with_names(directory: Path, type: str):
    """Load and return directory with yaml files with file name as key."""
    return {file.stem: load_yaml_file(file) for file in get_directory_paths(directory, type)}


def load_json_file(path: Path, _include_age: bool = False):
    """Read JSON file and return Python dictionary."""
    try:
        return load_json(read_file(path))
    except SystemExit as error:
        log.error("failed to load JSON file: %s", path)
        raise SystemExit(1) from error


def load_json_file_with_age(file_name: Path):
    """Read JSON file and return Python dictionary, include age property."""
    try:
        result = load_json(read_file(file_name))
        modified_time = os.path.getmtime(file_name)
        file_age_in_seconds = time.time() - modified_time

        result["age"] = convert(file_age_in_seconds, "seconds", "human")
        return result
    except SystemExit as error:
        log.error("failed to load JSON file: %s", file_name)
        raise SystemExit(1) from error


def load_json_directory_with_age(path: Path):
    """Read directory with JSON files and return single Python dictionary."""
    return sort_dictionary({file: load_json_file_with_age(file) for file in path.iterdir() if file.is_file()})


def read_file(file_name: Path):
    """Read file and return file content as string."""
    try:
        return file_name.expanduser().read_text()
    except IOError as error:
        log.error("failed to read file (%s)", error)
        raise SystemExit(1) from error


def read_yaml_file(file_name: Path):
    """Read YAML file, return Python object."""
    return yaml.safe_load(read_file(file_name))


def write_yaml_file(file_name: Path, data: Any):
    """Write data to YAML file."""
    file_name.write_text(yaml.safe_dump(data))


def write_file(file_name: Path, content: str, quiet=False):
    """Write or append content to file, if content is not of type string convert it to JSON."""
    path = file_name.expanduser()
    create_parent_directory(path)

    if not quiet:
        log.info(":floppy_disk: writing file %s", path)

    path.write_text(content)


def create_yaml_file(file_name: Path, data=None):
    """Create YAML file and directory, when they don't exist."""
    if not file_name.exists():
        create_parent_directory(file_name)
        if data is None:
            with open(file_name, "w") as file_pointer:
                file_pointer.write("---\n\n{}\n")
        else:
            write_file(file_name, yaml.safe_dump(data))


def yaml_file_append(file_name: Path, value: Any):
    """Extend list in YAML file."""
    create_yaml_file(file_name, [])

    data = yaml.safe_load(read_file(file_name))
    data.append(value)
    write_yaml_file(file_name, list(set(data)))


def write_json_file(file_name: Path, content: dict[Any, Any] | list[Any], mode: WriteFlags = WriteFlags.write):
    """Write JSON file."""
    log.info(":floppy_disk: writing JSON file: %s", file_name)
    with open(file_name.expanduser(), mode, encoding="utf-8") as file_pointer:
        file_pointer.write(json.dumps(content))


def list_dir(path: Path):
    """Return path iterator with Paths in path when path exists and is directory."""
    return path.iterdir() if path.is_dir() else []


def create_directory(directory: Path):
    """Create directory if directory not exists."""
    if not directory.is_dir():
        log.info(":file_folder: creating directory: %s", directory)
        directory.expanduser().mkdir(parents=True)


def create_parent_directory(directory: Path):
    """Create parent directory if directory not exists."""
    create_directory(directory.parent)


def delete_directory(path: Path):
    """Delete directory if directory exists."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        log.info(":file_folder: directory already vanished: %s", path)


def delete_cache_directories(directories: list[Path], force: bool = False):
    """Delete cache directories."""
    if not force:
        console.print(":warning: The following directories will be deleted:")
        for cache_directory in directories:
            console.print(f" - {cache_directory}")
        console.print()

    if force or Confirm.ask("Are you sure?"):
        log.info(":toilet: clearing cache directories")
        for cache_directory in directories:
            delete_directory(cache_directory)


def glob_directory_files(directory: Path, pattern: str = "**/*"):
    """Glob files in directory."""
    if not directory.is_dir():
        log.error(":person_facepalming: directory not found: %s", directory)
        raise SystemExit(1)

    files = list(filter(Path.is_file, directory.glob(pattern)))

    if not files:
        log.warning(":person_facepalming: no files matched in directory: %s", directory)
        raise SystemExit(0)

    return files


def clear_file(path: Path):
    """Delete content of a file."""
    with open(path, "r+") as file_pointer:
        file_pointer.truncate(0)
        file_pointer.close()


def bytes_to_human(bytes: float):
    """Return human size from bytes."""
    size_suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]

    index = 0
    while bytes >= 1024 and index < len(size_suffixes) - 1:
        bytes /= 1024.0
        index += 1

    return f'{("%.2f" % bytes).rstrip("0").rstrip(".")} {size_suffixes[index]}'


def get_removable_block_devices():
    """Return a list with removable block devices."""
    fields = [
        "NAME",
        "LABEL",
        "SIZE",
        "PARTLABEL",
        "FSTYPE",
        "MODEL",
        "TYPE",
        "STATE",
        "VENDOR",
        "HOTPLUG",
        "MOUNTPOINT",
    ]

    lsblk_result = shell("lsblk", "-J", "-p", "--output", ",".join(fields))

    all_devices = json.loads(lsblk_result.decode())

    devices = []
    for device in all_devices["blockdevices"]:
        pprint(device)
        if device["hotplug"]:
            if device["vendor"]:
                vendor = device["vendor"].strip().capitalize()
            else:
                vendor = "Unknown"

            if device["model"]:
                model = device["model"].strip()
            else:
                model = "Unknown"

            _device = {"name": device["name"], "model": "{}, {}".format(vendor, model), "size": device["size"]}

            if "partitions" in device:
                partitions = {}
                for child in device["children"]:
                    if child["type"] != "part":
                        continue
                    partition_string = "{size} (fstype: {fstype}, label: {label})"
                    partitions[child["name"]] = partition_string.format(**child)
                _device["partitions"] = partitions

            devices.append(_device)
    print("#########################")
    print(devices)
    return devices


def render_template(template_file, destination_file, template_vars, chmod):
    """Render a template file."""
    template = string.Template(read_file(template_file))
    write_file(destination_file, template.substitute(template_vars))
    if chmod:
        os.chmod(destination_file, int(str(chmod), 8))


def download(url, destination):
    """Download file to destination."""
    destination_path = destination.rsplit("/", 1)[0]
    create_directory(destination_path)

    if os.path.isfile(destination):
        print(f"- destination file found: {destination}")
    else:
        subprocess.call(["wget", "--directory-prefix", destination_path, "--content-disposition", url])


def untar(source, destination, path=None):
    """Untar an archive."""
    create_directory(destination)
    print(f'- extracting: {source.rsplit("/", 1)[1]} to {destination})')
    if path:
        shell("tar", "--strip-components", "1", "-xf", source, "-C", destination, path)
    else:
        shell("tar", "-xf", source, "-C", destination)


def requires_superuser_rights():
    """Exit if user does not have root permissions."""
    if os.geteuid() != 0:
        print("This script needs superuser rights to run,")
        print("try to run it with sudo or become root...")
        raise SystemExit(1)


def mount(device, mount_point):
    """Mount a partition."""
    shell("mount", device, mount_point)


def unmount(device):
    """Unmount a partition."""
    shell("mount", device)


def confirm_write(block_device):
    """Confirm writing image to SD card."""
    target_device = block_device["name"]
    msg = [
        "CAUTION\n",
        f"if you continue all data on device: {target_device}",
        "will be overwritten, THIS IS IRREVERSIBLE!!!",
    ]
    banner("\n".join(msg))
    print("* Device which will be overwritten:\n")
    print(f"{block_device['model']} ({block_device['size']})")
    print(f"\n*{block_device['name']}:")
    if block_device["partitions"]:
        for partition, description in block_device["partitions"].items():
            print(f"  {partition}: {description}")
    print('\ntype "yes" to write image to SD or enter any other to exit:')
    response = input("-> ")
    if response == "yes":
        return True

    return False


def select():
    """Select block device to write to."""
    banner("Select target block device (SD Card).")
    block_devices = get_removable_block_devices()

    if not block_devices:
        print("\ncould not find any removable block device for writing")
        print("please insert media and try again...")
        raise SystemExit(1)

    plural = "" if len(block_devices) == 1 else "s"
    print(f"- found {len(block_devices)} removable device{plural}:")
    for index, device in enumerate(block_devices):
        description = "  {index}: {name} ({size}) ({model})"
        print(description.format(index=index, **device))

    print("")
    print("choose the target device (anything else will abort):")
    response = input("-> ")
    try:
        block_device_number = int(response)
        if block_device_number not in range(0, len(block_devices)):
            raise ValueError
    except ValueError:
        print("\ncancelled operation, will exit now...")
        raise SystemExit(1)
    else:
        device = block_devices[block_device_number]
        banner(f'selected target device -> {device["name"]}')
        return device


def prepare_generic(block_device):
    """
    Prepare media.

    To dump partition table:
        sudo sfdisk -d /dev/mmcblk0 > ./files/partition_table
    """
    print("- zapping removable media")
    shell("wipefs", "--all", "--force", block_device["name"])
    shell("sgdisk", "--zap-all", block_device["name"])
    shell("sgdisk", "--clear", block_device["name"])

    # Partition 1 - Use the last 200MB, set partition type to ESP,
    # enable the legacy boot attribute
    shell("sgdisk", "--new=1:0:+200M", "--typecode=1:ef00", "--attributes=1:set:2", block_device["name"])

    # Partition 2 - Use the whole partition size, except the last 200MB,
    # set partition type to Linux
    shell("sgdisk", "--largest-new=2", "--typecode=2:8300", block_device["name"])

    os.system("partprobe")

    print("- creating vfat file system on boot partition")
    if Path(block_device["name"] + "1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "1")
    elif Path(block_device["name"] + "p1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "p1")

    print("- creating ext4 file system on root partition")
    if Path(block_device["name"] + "2").is_block_device():
        shell("mkfs.ext4", "-O", "^has_journal", block_device["name"] + "2")
    elif Path(block_device["name"] + "p2").is_block_device():
        shell("mkfs.ext4", "-O", "^has_journal", block_device["name"] + "p2")

    # https://gist.github.com/elerch/678941eb670324ffc3f261eabba81310


def prepare(block_device):
    """
    Prepare SD card.

    To dump partition table:
        sudo sfdisk -d /dev/mmcblk0 > ./files/partition_table
    """
    print("- zapping removable media")
    shell("wipefs", "--all", "--force", block_device["name"])
    shell("sgdisk", "--zap-all", block_device["name"])

    # print('- creating partitions')
    # shell(
    #     'sgdisk', '--new=1:0:+256M', '--typecode=1:0700', '-c1:boot', block_device['name'])
    # print('- creating paritions')
    # shell(
    #     'sgdisk', '--largest-new=2', '--typecode=2:8300', '-c2:arch', block_device['name'])
    # partition_table = os.path.join('paths']['files'], 'partition_table')
    # os.system(f'sfdisk --wipe=always
    # --wipe-partitions=always {block_device["name"]} < ./files/partition_table')

    print("- creating partition tables")
    os.system(f'sfdisk {block_device["name"]} < ./files/partition_table')
    os.system("partprobe")

    print("- creating vfat file system on boot partition")
    if Path(block_device["name"] + "1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "1")
    elif Path(block_device["name"] + "p1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "p1")

    print("- creating ext4 file system on root partition")
    if Path(block_device["name"] + "2").is_block_device():
        shell("mkfs.ext4", "-O", "^has_journal", block_device["name"] + "2")
    elif Path(block_device["name"] + "p2").is_block_device():
        shell("mkfs.ext4", "-O", "^has_journal", block_device["name"] + "p2")


def unmount_advanced():
    """Unmount mounted paths."""
    mounted_devices = []
    for partition in psutil.disk_partitions():
        if partition.mountpoint.startswith("/tmp/awakenodes"):
            mounted_devices.append(partition.mountpoint)
    mounted_devices.reverse()
    for device in mounted_devices:
        shell("umount", device)


# def _mount_image(image_file, partition, bytes_offset):
#     """Mount boot and root partitions from a raw image file."""
#     mount_point = cfg['paths']['mount_point_{}'.format(partition)]
#     if not os.path.isdir(mount_point):
#         log.info('creating mount point directory: %s', mount_point)
#         os.makedirs(mount_point)
#     shell('mount', '-v', '-o', 'offset={}'.format(bytes_offset),
#                 image_file, mount_point)

# def writexx(fqdn, block_device):
#     """Prepare SD card."""
#     image_file = os.path.join(cfg['paths']['images'], '{}.img'.format(fqdn))
#     target_device_name = block_device['name']
#     if confirm_write(block_device):
#         _write_image(image_file, target_device_name)
#         _grow_partition(target_device_name)
#         # print('rescannning device partition table')
#         # shell('partprobe' target_device_name)
#         print('ejecting SD card: {}'.format(target_device_name))
#         shell('eject', target_device_name)
#         print('done, SD card is ready for: {}'.format(fqdn))
#
# def _write_image(image_file, target):
#     """Write an image with dd."""
#     utils.banner('writing image to block device (SD card)')
#     print('* {} -> {}'.format(image_file, target))
#     print('* this will probably take a while...\n')
#     cmd = ['dd', 'if={}'.format(image_file), 'of={}'.format(target),
#            'bs=4M', 'status=progress']
#     print('running command: {}'.format(' '.join(cmd)))
#     subprocess.call(cmd)
#
#     # dd_process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
#     # while dd_process.poll() is None:
#     #     time.sleep(0.5)
#     #     dd_process.send_signal(signal.SIGUSR1)
#     #     while True:
#     #         line = dd_process.stderr.readline()
#     #     if 'records in' in line:
#     #         print(line[:line.index('+')], 'records',)
#     #     if 'bytes' in line:
#     #         print(line.strip(), '\r',)
#     #         break
#     # print(dd_process.stderr.read())
#
#
# def _grow_partition(target_device_name):
#     """Grow partition size to the max."""
#     utils.banner('grow system partition')
#     print('* growing {}'.format(target_device_name))
#     partitions = shell('parted', target_device_name, '-ms', 'unit s p')
#     partition = next((partition
#                       for partition in partitions.decode().split('\n')
#                       if partition.startswith('2:')))
#     system_partition_offset = int(partition.split(':')[1].rstrip('s'))
#     cmd = 'printf "d\n2\nn\np\n2\n{}\n\np\nw\n" | fdisk {}'
#     os.system(cmd.format(system_partition_offset, target_device_name))

# def _get_partition_offsets(file_output):
#     """Return partitions with offsets in bytes."""
#     byte_offsets = {}
#     lines = str(file_output).split(';')[1:]
#     for line in lines:
#         line = line.strip()
#         partition = line.split(':')[0].strip()
#         sector_offset = re.match('.*, startsector (.*),', line).groups(0)[0]
#         byte_offsets[partition] = 512 * int(sector_offset)
#     return byte_offsets

# def mount(path):
#     """Mount boot and root partitions from raw image file or SD card."""
#     if not os.path.exists(path):
#         log.critical('path does not exist: %s', path)
#         raise SystemExit(1)
#
#     file_output = shell('file', '-b', path)
#     if file_output.split()[0] == b'DOS/MBR':
#         byte_offsets = _get_partition_offsets(file_output)
#         _mount_image(path, 'boot', byte_offsets['partition 1'])
#         _mount_image(path, 'root', byte_offsets['partition 2'])
#     elif file_output.startswith(b'block special'):
#         print('sorry, not implemented yet.')
#     else:
#         log.critical('path should be an image file or block device')
#         raise SystemExit(1)
