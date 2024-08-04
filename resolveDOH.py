import json
import requests

domains = []
with open('domains-doh.txt', 'r') as f:
    domains = f.read().splitlines()

with open('ipv4-doh.txt', 'w') as ipv4_file, open('ipv6-doh.txt', 'w') as ipv6_file:
    for domain in domains:
        # Request for IPv4 (A) records
        url_ipv4 = f"https://dns.google/resolve?name={domain}&type=A"
        response_ipv4 = requests.get(url_ipv4)
        if response_ipv4.status_code == 200:
            data_ipv4 = json.loads(response_ipv4.text)
            if "Answer" in data_ipv4:
                for answer in data_ipv4["Answer"]:
                    if answer["type"] == 1:  # Type A (IPv4)
                        ipv4_file.write(f"{answer['data']} #{domain}\n")

        # Request for IPv6 (AAAA) records
        url_ipv6 = f"https://dns.google/resolve?name={domain}&type=AAAA"
        response_ipv6 = requests.get(url_ipv6)
        if response_ipv6.status_code == 200:
            data_ipv6 = json.loads(response_ipv6.text)
            if "Answer" in data_ipv6:
                for answer in data_ipv6["Answer"]:
                    if answer["type"] == 28:  # Type A (IPv4)
                        ipv6_file.write(f"{answer['data']} #{domain}\n")
