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
from rich.prompt import Confirm

from .console import console, log
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


def get_block_devices():
    """Return dict with block devices."""
    fields = [
        "NAME",
        "LABEL",
        "SIZE",
        "PARTLABEL",
        "UUID",
        "FSTYPE",
        "MODEL",
        "TYPE",
        "STATE",
        "VENDOR",
        "HOTPLUG",
        "MOUNTPOINT",
    ]

    lsblk_result = shell("lsblk", "--json", "--paths", "--output", ",".join(fields))

    if not lsblk_result:
        log.error(":persion_facepalming: lsblk response is empty")
        raise SystemExit(1)

    return json.loads(lsblk_result)


def get_removable_block_devices(excluded_uuids: list[str] | None = None, full=False):
    """Return list with removable block devices and partitions."""
    all_devices = get_block_devices()

    devices = []
    for device in all_devices["blockdevices"]:
        if not device["hotplug"]:
            continue

        if device["vendor"]:
            vendor = device["vendor"].strip().capitalize()
        else:
            vendor = "Unknown"

        if device["model"]:
            model = device["model"].strip()
        else:
            model = "Unknown"

        _device = {"name": device["name"], "model": f"{vendor}, {model}", "size": device["size"]}

        if "children" in device:
            partitions = {}
            for child in device["children"]:
                if child["type"] != "part":
                    continue

                if not excluded_uuids or child["uuid"] not in excluded_uuids:
                    if full:
                        partition_name = child["name"]
                        del child["name"]
                        partitions[partition_name] = child
                    else:
                        partition_string = "{size} (fstype: {fstype}, label: {label}, uuid: {uuid})"
                        partitions[child["name"]] = partition_string.format(**child)
            _device["partitions"] = partitions

        if _device["partitions"]:
            devices.append(_device)

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


def get_mount_point_devices(device: Path, mount_point: Path):
    """Return mount point devices."""
    return [
        partition
        for partition in psutil.disk_partitions()
        if partition.device == str(device) and partition.mountpoint == str(mount_point)
    ]


def get_device_mount_points(mount_point: Path):
    """Return mount points."""
    return [partition for partition in psutil.disk_partitions() if partition.mountpoint == str(mount_point)]


def verify_mount(device: Path, mount_point: Path):
    """Return True when mounted, False when unmounted, exit when mismatch."""
    if not mount_point.is_mount():
        return False

    device_mount_points = get_device_mount_points(mount_point)

    if len(device_mount_points) > 1:
        device_mount_points = [mount_point.device for mount_point in device_mount_points]
        log.critical(
            ":scream_cat: multiple devices are mounted on %s (%s)", mount_point, " & ".join(device_mount_points)
        )
        raise SystemExit(1)

    if not mount_point:
        log.critical(":scream_cat: expected device %s to be mounted on instead of %s", device, mount_point)
        raise SystemExit(1)

    log.info(":floppy_disk: device %s is already mounted :smile: on %s", device, mount_point)

    return True


def mount(device: Path, mount_point: Path):
    """Mount device."""
    if verify_mount(device, mount_point):
        return

    shell("sudo", "mount", str(device), str(mount_point))


def unmount(device: Path):
    """Unmount a partition."""
    if not device.is_mount():
        log.info("device is not mounted: %s", device)
        return

    shell("sudo", "umount", str(device))


def __banner(text: str):
    """Show text banner."""
    print("\n" + 59 * "*")

    if isinstance(text, list):
        for line in text:
            print(line)
    else:
        print(text)
    print(59 * "*" + "\n")


def confirm_write(block_device):
    """Confirm writing image to SD card."""
    target_device = block_device["name"]
    msg = [
        "CAUTION\n",
        f"if you continue all data on device: {target_device}",
        "will be overwritten, THIS IS IRREVERSIBLE!!!",
    ]
    __banner("\n".join(msg))
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
    __banner("Select target block device (SD Card).")
    block_devices = get_removable_block_devices()

    if not block_devices:
        log.info(":person_facepalming: could not find any removable block device for writing")
        log.info(":floppy_disk: please insert media and try again...")
        raise SystemExit(1)

    plural = "" if len(block_devices) == 1 else "s"
    log.info(":sleuth_or_spy: found {%s} removable device{%s}:", len(block_devices), plural)
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
        log.info("cancelled operation, will exit now...")
        raise SystemExit(1)
    else:
        device = block_devices[block_device_number]
        __banner(f'selected target device -> {device["name"]}')
        return device


def prepare_generic(block_device):
    """
    Prepare media.

    Dump partition table:
        sudo sfdisk -d /dev/mmcblk0 > ./files/partition_table
    """
    log.info(":toilet: zapping removable media")
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

    log.info(":floppy_disk: creating vfat file system on boot partition")
    if Path(block_device["name"] + "1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "1")
    elif Path(block_device["name"] + "p1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "p1")

    print(":floppy_disk: creating ext4 file system on root partition")
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
    log.info(":toilet: zapping removable media")
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

    log.info(":table_tennis_paddle_and_ball: creating partition tables")
    os.system(f'sfdisk {block_device["name"]} < ./files/partition_table')
    os.system("partprobe")

    log.info(":floppy_disk: creating vfat file system on boot partition")
    if Path(block_device["name"] + "1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "1")
    elif Path(block_device["name"] + "p1").is_block_device():
        shell("mkfs.vfat", block_device["name"] + "p1")

    log.info(":floppy_disk: creating ext4 file system on root partition")
    if Path(block_device["name"] + "2").is_block_device():
        shell("mkfs.ext4", "-O", "^has_journal", block_device["name"] + "2")
    elif Path(block_device["name"] + "p2").is_block_device():
        shell("mkfs.ext4", "-O", "^has_journal", block_device["name"] + "p2")


def unmount_tree(root: Path):
    """Unmount mounts from given root path."""
    mounted_devices = []

    for partition in psutil.disk_partitions():
        if partition.mountpoint.startswith(str(root)):
            mounted_devices.append(partition.mountpoint)

    if not mounted_devices:
        log.info(":palm_tree: no mounted devices found in: %s", root)
        return

    mounted_devices.reverse()
    for device in mounted_devices:
        shell("sudo", "umount", device)


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
#     utils.__banner('writing image to block device (SD card)')
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
#     utils.__banner('grow system partition')
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
