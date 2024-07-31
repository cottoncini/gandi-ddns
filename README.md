# gandi-ddns
Dynamic DNS with Gandi LiveDNS.

## Purpose
Keep a DNS record pointing to the current IP addresses of the host.

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
Set environment variables:
```bash
export GANDI_DDNS_BASE_URL="https://api.gandi.net/v5/livedns/domains"
export GANDI_DDNS_TOKEN=<your_token>
export GANDI_DDNS_DOMAIN=<your_domain>
export GANDI_DDNS_SUBDOMAIN=<your_subdomain>
export GANDI_DDNS_TTL=900
```
Run the script:
```bash
python gandi-ddns.py
```