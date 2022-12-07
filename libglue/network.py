"""libGlue network library."""

import xmltodict

from .shell import run_command

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


def ip_scan(ip_range: str):
    """Scan IP addresses and return dictionary."""
    xml_response = run_command(f"sudo nmap -sP {ip_range} -oX -").stdout.decode()

    result = []
    for host in xmltodict.parse(xml_response, dict_constructor=dict, force_list=("address",), attr_prefix="")[
        "nmaprun"
    ]["host"]:
        item = {"state": host["status"]["state"]}

        if "hostnames" in host and host["hostnames"]:
            item["name"] = host["hostnames"]["hostname"]["name"]

        for address in host["address"]:
            item[address["addrtype"]] = address["addr"]
            if address["addrtype"] == "mac" and "vendor" in address:
                item["vendor"] = address["vendor"]

        result.append(item)

    return result
