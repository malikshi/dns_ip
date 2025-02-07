import json
import requests
import subprocess
import ipaddress

# DNS server configuration
dns_servers = [
    {
        "name": "Google",
        "url": "https://dns.google/resolve?name={}&type={}",
        "headers": {}
    },
    {
        "name": "Cloudflare",
        "url": "https://cloudflare-dns.com/dns-query?name={}&type={}",
        "headers": {"accept": "application/dns-json"}
    }
]

# Function to resolve a domain for both A and AAAA records
def resolve_domain(domain):
    results = {
        'A': set(),    # Use a set to avoid duplicates
        'AAAA': set()  # Use a set to avoid duplicates
    }

    for server in dns_servers:
        for record_type in ["A", "AAAA"]:
            try:
                url = server["url"].format(domain, record_type)
                response = requests.get(url, headers=server["headers"])

                if response.status_code == 200:
                    data = response.json()
                    # Log the entire response for debugging
                    # print(f"Response from {server['name']} for {domain} ({record_type}): {data}")

                    # Check if 'Answer' exists and is a list
                    if "Answer" in data and isinstance(data["Answer"], list):
                        for answer in data["Answer"]:
                            # Ensure the answer is a dict and has the expected fields
                            if isinstance(answer, dict) and 'type' in answer and 'data' in answer:
                                if (record_type == "A" and answer["type"] == 1) or (record_type == "AAAA" and answer["type"] == 28):
                                    # Validate IP address before adding
                                    ip = answer['data']
                                    if validate_ip(ip, record_type):
                                        results[record_type].add(f"{ip} #{domain}")  # Add to set
                                    else:
                                        print(f"Invalid IP {ip} for {record_type} from {server['name']}")

                    else:
                        print(f"No answers found for {domain} with {server['name']}: {data}")

                else:
                    print(f"Unexpected response status {response.status_code} for {domain} with {server['name']}")

            except requests.RequestException as e:
                print(f"Error resolving {domain} with {server['name']}: {e}")
            except Exception as e:
                print(f"Error processing domain {domain}: {e}")

    # If no answers found, try using the dig command as a fallback
    if not results['A'] or not results['AAAA']:
        print(f"Trying dig command for {domain} as a fallback")
        for record_type in ["A", "AAAA"]:
            try:
                # Construct the dig command
                cmd = ["dig", "+short", record_type, domain]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                output = result.stdout.strip().splitlines()

                for line in output:
                    if validate_ip(line, record_type):
                        results[record_type].add(f"{line} #{domain}")
                    else:
                        print(f"Invalid IP {line} for {record_type} from dig command.")

            except subprocess.CalledProcessError as e:
                print(f"Error executing dig for {domain}: {e}")

    return results

def validate_ip(ip, record_type):
    """ Validate if the IP is a valid IPv4 or IPv6 address. """
    try:
        if record_type == "A":
            ipaddress.ip_address(ip)  # This will raise an error if it's not a valid IP
            return True
        elif record_type == "AAAA":
            ipaddress.ip_address(ip)  # This will raise an error if it's not a valid IP
            return True
    except ValueError:
        return False

# Read domains from file
with open('domains-doh.txt', 'r') as f:
    domains = f.read().splitlines()

# Resolve domains sequentially
with open('ipv4-doh.txt', 'w') as ipv4_file, open('ipv6-doh.txt', 'w') as ipv6_file:
    for domain in domains:
        results = resolve_domain(domain)
        if results['A']:
            ipv4_file.writelines("\n".join(results['A']) + "\n")
        if results['AAAA']:
            ipv6_file.writelines("\n".join(results['AAAA']) + "\n")