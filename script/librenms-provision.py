#!/usr/bin/env python3

import argparse
import sys
import requests
import dotenv

AUTH_ALGO = "-auth-algo"
AUTH_NAME = "-auth-name"
AUTH_SECRET = "-auth-secret"
CRYPT_ALGO = "-crypto-algo"
CRYPT_SECRET = "-crypto-secret"
HOSTNAME = "-hostname"

config = dotenv.dotenv_values()
api_key = config["LIBRENMS_API_KEY"]
LIBRENMS = config["LIBRENMS_ENDPOINT"]
reqs = requests.Session()
reqs.headers.update(
    {"X-Auth-Token": api_key},
)

def main():
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument(
        AUTH_ALGO,
        nargs=1,
        type=str,
        required=True,
        help="The authentication algorithm to be used",
    )
    parser.add_argument(
        AUTH_NAME,
        nargs=1,
        type=str,
        required=True,
        help="The authentication name to be used",
    )
    parser.add_argument(
        AUTH_SECRET,
        nargs=1,
        type=str,
        required=True,
        help="The authentication secret to be used",
    )
    parser.add_argument(
        CRYPT_ALGO,
        nargs=1,
        type=str,
        required=True,
        help="The authentication algorithm to be used",
    )
    parser.add_argument(
        CRYPT_SECRET,
        nargs=1,
        type=str,
        required=True,
        help="The authentication secret to be used",
    )
    parser.add_argument(
        HOSTNAME,
        nargs=1,
        type=str,
        required=True,
        help="The hostname of the device in librenms",
    )

    arguments = parser.parse_args()
    arguments_dict = arguments.__dict__
    get_value = lambda name: arguments_dict[name[1:].replace("-", "_")][0]

    auth_algo = get_value(AUTH_ALGO)
    auth_secret = get_value(AUTH_SECRET)
    auth_name = get_value(AUTH_NAME)
    crypto_algo = get_value(CRYPT_ALGO)
    crypt_secret = get_value(CRYPT_SECRET)
    hostname = get_value(HOSTNAME)

    response = reqs.get(f"{LIBRENMS}/api/v0/devices/{hostname}")
    response = response.json()
    if response["status"] == "error":
        print("Device doesn't exist, creating it.")
        # the device doesn't exist
        reqs.post(
            f"{LIBRENMS}/api/v0/devices",
            json={
                "hostname": hostname,
                "snmpver": "v3",
                "authlevel": "authPriv",
                "authname": auth_name,
                "transport": "udp",
                "authpass": auth_secret,
                "authalgo": auth_algo,
                "cryptopass": crypt_secret,
                "cryptoalgo": crypto_algo,
                "force_add": True,
            },
        ).raise_for_status()
    elif response["status"] == "ok":
        device = response["devices"][0]

        is_different = (
            device["authlevel"] != "authPriv"
            or device["snmpver"] != "v3"
            or device["authname"] != auth_name
            or device["authpass"] != auth_secret
            or device["authalgo"] != auth_algo
            or device["cryptopass"] != crypt_secret
            or device["cryptoalgo"] != crypto_algo
        )

        if is_different:
            reqs.patch(
                f"{LIBRENMS}/api/v0/devices/{hostname}",
                json={
                    "field": [
                        "authlevel",
                        "snmpver",
                        "authname",
                        "authpass",
                        "authalgo",
                        "cryptopass",
                        "crytoalgo",
                    ],
                    "data": [
                        "authPriv",
                        "v3",
                        auth_name,
                        auth_secret,
                        auth_algo,
                        crypt_secret,
                        crypto_algo,
                    ],
                },
            ).raise_for_status()


if __name__ == "__main__":
    main()
