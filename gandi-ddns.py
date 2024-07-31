import json
import logging
import os
from io import BytesIO

import pycurl


class APIError(Exception):
    """Exception raised for errors in API calls."""


def api_call(url, method="GET", body=None, header=None, ip_version=None):
    """Perform an API call."""

    buffer = BytesIO()
    curl = pycurl.Curl()

    if method == "POST" and body:
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.POSTFIELDS, body)
    if method == "DELETE":
        curl.setopt(pycurl.CUSTOMREQUEST, "DELETE")
    if header is not None:
        curl.setopt(pycurl.HTTPHEADER, header)
    if ip_version is not None:
        curl.setopt(pycurl.IPRESOLVE, ip_version)

    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.WRITEDATA, buffer)

    try:
        curl.perform()
    except pycurl.error as err:
        raise APIError(err.args[1]) from err

    code = curl.getinfo(curl.RESPONSE_CODE)
    response = buffer.getvalue().decode("UTF-8").strip()
    curl.close()
    return code, response


def get_new_ip(version):
    """Get current IP address."""

    RESOLVER_URL = "http://me.gandi.net/"
    log = logging.getLogger()
    try:
        code, ip = api_call(RESOLVER_URL, ip_version=version)
        if code == 200:
            log.debug(f"Got current IP {ip}.")
            return ip
        else:
            raise APIError(f"Request returned {code}.")

    except APIError as err:
        log.error(f"Failed to get current IP. {err}")
        raise


def get_old_ip(url, token):
    """Get old IP address from DNS record."""

    log = logging.getLogger()
    try:
        code, response_str = api_call(url, header=[f"Authorization: Bearer {token}"])
        response = json.loads(response_str)
        match code:
            case 404:
                log.debug("No existing record found.")
                return None
            case 200:
                log.debug("Existing record found.")
                return response["rrset_values"][0]
            case _:
                raise APIError(response["message"])
    except APIError as err:
        log.error(f"Failed to get record. {err}")
        raise


def add_record(url, ip, ttl, token):
    """Add new DNS record."""

    log = logging.getLogger()
    try:
        code, response_str = api_call(
            url,
            method="POST",
            body=json.dumps({"rrset_ttl": ttl, "rrset_values": [ip]}),
            header=[
                f"Authorization: Bearer {token}",
                "Content-Type: application/json",
            ],
        )
        response = json.loads(response_str)
        match code:
            case 201:
                log.debug(f"Added record with IP {ip}.")
            case 200:
                log.warning(f"Record already present with IP {ip}.")
            case _:
                raise APIError(response["message"])
    except APIError as err:
        log.error(f"Failed to add new record. {err}")
        raise


def delete_record(url, token):
    """Delete existing DNS record."""

    log = logging.getLogger()
    try:
        code, response_str = api_call(
            url,
            method="DELETE",
            header=[
                f"Authorization: Bearer {token}",
            ],
        )
        response = json.loads(response_str)
        match code:
            case 204:
                log.info("Deleted existing record.")
            case _:
                raise APIError(response["message"])
    except APIError as err:
        log.error(f"Failed to delete existing record. {err}")
        raise


def update_record(record_type, ip_version):
    """Update DNS record with current IP address."""

    log = logging.getLogger()
    try:
        api_url = "/".join(
            [
                os.environ["GANDI_DDNS_BASE_URL"],
                os.environ["GANDI_DDNS_DOMAIN"],
                "records",
                os.environ["GANDI_DDNS_SUBDOMAIN"],
                record_type,
            ]
        )
        api_token = os.environ["GANDI_DDNS_TOKEN"]
        ttl = os.environ["GANDI_DDNS_TTL"]

        new_ip = get_new_ip(ip_version)
        old_ip = get_old_ip(api_url, api_token)

        if old_ip is None:
            add_record(api_url, new_ip, ttl, api_token)
        elif old_ip != new_ip:
            delete_record(api_url, api_token)
            add_record(api_url, new_ip, ttl, api_token)
        log.info(f"Successfully updated record {record_type} with IP {new_ip}.")

    except APIError:
        log.error(f"Could not update record {record_type}.")

    except KeyError as err:
        log.error(f"Missing environment variable {err}.")


if __name__ == "__main__":
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    log.addHandler(handler)

    update_record("A", pycurl.IPRESOLVE_V4)
    update_record("AAAA", pycurl.IPRESOLVE_V6)

    logging.shutdown()
