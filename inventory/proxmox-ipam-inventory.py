#!/usr/bin/env python3

import requests
import ipaddress
import json
import dotenv

def main():
    pass

config = dotenv.dotenv_values()
proxmox_host = config["PROXMOX_URL"]
api_key = config["PROXMOX_API_KEY"]
reqs = requests.Session()
reqs.headers.update(
    {"Authorization": api_key},
)


def do_req(request):
    request.raise_for_status()
    return request


vms, ipam = [
    do_req(request).json()
    for request in [
        reqs.get(f"{proxmox_host}/api2/json/cluster/resources"),
        reqs.get(f"{proxmox_host}/api2/json/cluster/sdn/ipams/pve/status"),
    ]
]

inventory = {
    "_meta": {
        "hostvars": {},
    },
    "lxc": {"hosts": [], "vars": {"ansible_user": "root"}},
    "qemu": {"hosts": [], "vars": {"ansible_user": "matthieu"}},
    "vms": {
        "children": ["lxc", "qemu"],
    },
    "pve": {
        "hosts": ["10.80.255.2", "10.80.255.200", "10.80.255.201", "10.80.255.202"],
        "vars": {"ansible_connection": "ssh", "ansible_user": "root"},
    },
}

vmIpamDict = {}
for record in ipam["data"]:
    valid = "vmid" in record and "ip" in record
    if not valid:
        continue
    if record["vmid"] in vmIpamDict:
        vmIpamDict[record["vmid"]].append(record["ip"])
    else:
        vmIpamDict[record["vmid"]] = [record["ip"]]

for vm in vms["data"]:
    valid = (
        "type" in vm
        and vm["type"] in ["lxc", "qemu"]
        and "status" in vm
        and vm["status"] == "running"
        and "name" in vm
    )
    if not valid:
        continue

    # We only use the IPv4 IPs for Ansible since the IPv6 evpn fabric is still unstable
    # because of the evpn redistribution issue.

    if f"{vm['vmid']}" in vmIpamDict:
        ipamIPs = [
            ip
            for ip in [ipaddress.ip_address(ip) for ip in vmIpamDict[f"{vm['vmid']}"]]
            if ip.version == 4
        ]
        fqdn = f"{vm['name']}.pantheon.lab.mpgn.dev"
        type_ = vm["type"]

        for ip in ipamIPs:
            inventory[type_]["hosts"].append(fqdn)
            inventory["_meta"]["hostvars"][fqdn] = {
                "ansible_host": str(ip),
            }

print(json.dumps(inventory))
