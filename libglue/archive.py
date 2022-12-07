#!/usr/bin/env python3

"""Archive library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

import binascii
import hashlib
import os
import shutil
import zipfile
import zlib
from pathlib import Path
from shutil import move

import py7zr
from rich.progress import Progress, TaskID

from .console import log

extensions = ["7z", "zip"]
offsets = {}  # {'a78': 128, 'lnx': 64, 'nes': 16}


def append_to_zip(zip_path: Path, path: Path, name: str):
    """Append file to archive."""
    with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as _target:
        _target.write(path, name)


def extract_file(zip_path: Path, name: str, destination: Path):
    """Extract file from archive."""
    with zipfile.ZipFile(zip_path, "r", zipfile.ZIP_DEFLATED) as zip:
        zip.extract(name, destination)


def delete_file_from_zip(zip_path: Path, name: str):
    """Delete file from Zip archive."""
    log.info("delete file from archive: %s (%s)", name, zip_path)

    temp_file = "/tmp/temp.zip"
    with zipfile.ZipFile(zip_path, "r") as source_zip:
        with zipfile.ZipFile(temp_file, "w") as temp_zip:
            for item in source_zip.infolist():
                buffer = source_zip.read(item.filename)
                if item.filename != name:
                    temp_zip.writestr(item, buffer)
            temp_zip.close()
            source_zip.close()

    log.info("moving: %s -> %s", temp_file, zip_path)
    move(temp_file, zip_path)


def get_zip_checksums(path: Path, task_id: TaskID, progress: Progress):
    """Open zip file and returns a sha1 checksum of all the members of the zip."""
    checksums = {}

    with zipfile.ZipFile(path) as zip_archive:
        names = zip_archive.namelist()

        progress.start_task(task_id)
        progress.update(task_id, visible=True, description=path.name, total=len(names))

        for name in names:
            progress.update(task_id, description=f"[magenta]{path.stem}[/]/[cyan]{name}")
            with zip_archive.open(name) as member_file:
                member_content = member_file.read()

            sha1_checksum = hashlib.sha1(member_content).hexdigest()
            checksums[name] = sha1_checksum
            progress.update(task_id, advance=1)

    return checksums


def append(path, sources):
    """Append to archive."""
    with zipfile.ZipFile(path, "a", zipfile.ZIP_DEFLATED) as _target:
        for source_archive, source_roms in sources.items():
            with zipfile.ZipFile(source_archive, "r") as _source:
                for file in _source.filelist:
                    if file.filename in source_roms:
                        _target.writestr(source_roms[file.filename], _source.read(file.filename))


def _temp_archive_name(path):
    return f"{path}___scanomatic_temp"


def create(path, sources):
    """Create archive."""
    with zipfile.ZipFile(_temp_archive_name(path), mode="w", allowZip64=True) as _temp_archive:
        for source_archive, source_roms in sources.items():
            with zipfile.ZipFile(source_archive, "r") as source:
                for file in source.filelist:
                    if file.filename in source_roms:
                        _temp_archive.writestr(source_roms[file.filename], source.read(file.filename))

    shutil.move(_temp_archive_name(path), path)


def rename(path, names):
    """Rename files in archive."""
    with zipfile.ZipFile(path, "r") as source:
        with zipfile.ZipFile(_temp_archive_name(path), mode="w", allowZip64=True) as _temp_archive:
            for file in source.filelist:
                print(file.filename)
                if file.filename in names:
                    print("renaming:", file.filename, "->", names[file.filename])
                    _temp_archive.writestr(names[file.filename], source.read(file.filename))
                else:
                    _temp_archive.writestr(file.filename, source.read(file.filename))

    print("writing archive:", path)
    shutil.move(_temp_archive_name(path), path)


def scan_zip(path, md5=False, clean=False):
    """Scan ZIP archive."""
    try:
        with zipfile.ZipFile(path, mode="r", allowZip64=True) as archive:
            for info in archive.infolist():
                extension = info.filename[-3:]

                if extension in offsets:
                    offset = offsets[extension]
                    crc = binascii.crc32(archive.read(info.filename)[offset:]).lower()  #  & 0xFFFFFFFF
                else:
                    offset = 0
                    crc = hex(info.CRC)[2:].zfill(8).lower()

                size = info.file_size - offset

                result = {"path": path, "file_name": info.filename, "crc": crc, "size": str(size), "matches": []}

                if md5:
                    with archive.open(info.filename) as data:
                        file_hash = hashlib.md5()
                        while chunk := data.read(1024**2 * 16)[offset:]:  # read in chunks of 16MB
                            file_hash.update(chunk)
                        yield result | {"md5": file_hash.hexdigest()}
                else:
                    yield result
    except zipfile.BadZipFile as error:
        archive_file_size = os.path.getsize(path)

        if not archive_file_size:
            print(f"🚽 archive is 0 bytes (will delete): {path}")
            os.remove(path)
        elif clean:
            print(f"🚽 deleting corrupt archive: {path} (reason: {error})")
            os.remove(path)
        else:
            print(f"ERROR - archive ({error}): {path}")


def scan_7z(path, md5=False, clean=False):
    """Scan 7-Zip archive."""
    try:
        with py7zr.SevenZipFile(path, mode="r") as archive:
            for entry in archive.list():
                if md5:
                    print("implement md5 calculation for 7zip")

                yield {
                    "path": path,
                    "file_name": entry.filename,
                    "crc": hex(entry.crc32)[2:].zfill(8).lower(),
                    "size": str(entry.uncompressed),
                    "matches": [],
                }
    except (OSError, py7zr.Bad7zFile):
        print("error:", path, clean)


def file_crc(file_name):
    """Calculate file crc."""
    prev = 0

    for eachLine in open(file_name, "rb"):
        prev = zlib.crc32(eachLine, prev)

    crc = "%X" % (prev & 0xFFFFFFFF)
    return crc.lower()


def scan_file(path, md5=False, clean=False):
    """Scan ZIP or 7-Zip archive."""
    extension = path.split(".")[-1]

    if extension == "7z":
        for file in scan_7z(path, md5, clean):
            yield file | {"type": extension}
    elif extension == "zip":
        for file in scan_zip(path, md5, clean):
            yield file | {"type": extension}
    else:
        yield {"type": "file", "path": path, "crc": file_crc(path), "size": os.path.getsize(path)}


def scan_directory(directory, md5, clean):
    """Scan directory with archives."""
    result = []
    files = os.listdir(directory)
    total_files = len(files)

    for index, file_name in enumerate(files):
        for file in scan_file(os.path.join(directory, file_name), md5, clean):
            print(f"scanning archive: {index + 1} of {total_files}", end="\r")  # , flush=True
            result.append(file)

    return result
