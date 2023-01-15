"""libGlue network library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

import xmltodict

from .shell import shell


def ip_scan(ip_range: str):
    """Scan IP addresses and return dictionary."""
    xml_response = shell("sudo", "nmap", "-sP", ip_range, "-oX", "-")

    result = []
    for host in xmltodict.parse(
        xml_response, dict_constructor=dict, force_list=("address",), attr_prefix=""
    )["nmaprun"]["host"]:
        item = {"state": host["status"]["state"]}

        if "hostnames" in host and host["hostnames"]:
            item["name"] = host["hostnames"]["hostname"]["name"]

        for address in host["address"]:
            item[address["addrtype"]] = address["addr"]
            if address["addrtype"] == "mac" and "vendor" in address:
                item["vendor"] = address["vendor"]

        result.append(item)

    return result
