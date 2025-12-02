import json
import requests
import subprocess
import ipaddress
import concurrent.futures
import sys

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

# Use a global session to reuse TCP connections (Keep-Alive)
session = requests.Session()

def validate_ip(ip, record_type):
    """ Validate if the IP is a valid IPv4 or IPv6 address. """
    try:
        if record_type == "A":
            ipaddress.ip_address(ip)
            return True
        elif record_type == "AAAA":
            ipaddress.ip_address(ip)
            return True
    except ValueError:
        return False

# Function to resolve a domain for both A and AAAA records
def resolve_domain(domain):
    results = {
        'A': set(),
        'AAAA': set()
    }

    # Strip whitespace just in case
    domain = domain.strip()
    if not domain:
        return results

    for server in dns_servers:
        for record_type in ["A", "AAAA"]:
            try:
                url = server["url"].format(domain, record_type)
                # Use the global session for faster requests
                response = session.get(url, headers=server["headers"], timeout=5)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "Answer" in data and isinstance(data["Answer"], list):
                            for answer in data["Answer"]:
                                if isinstance(answer, dict) and 'type' in answer and 'data' in answer:
                                    if (record_type == "A" and answer["type"] == 1) or (record_type == "AAAA" and answer["type"] == 28):
                                        ip = answer['data']
                                        if validate_ip(ip, record_type):
                                            results[record_type].add(f"{ip} #{domain}")
                    except json.JSONDecodeError:
                        pass # Ignore JSON errors
            except requests.RequestException:
                pass # Ignore request errors for speed

    # Fallback to dig if API failed
    if not results['A'] or not results['AAAA']:
        for record_type in ["A", "AAAA"]:
            try:
                # Use subprocess to call dig
                cmd = ["dig", "+short", record_type, domain]
                # Timeout added to prevent hanging
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
                output = result.stdout.strip().splitlines()

                for line in output:
                    if validate_ip(line, record_type):
                        results[record_type].add(f"{line} #{domain}")

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

    return results

def main():
    # Read domains from file
    try:
        with open('domains-doh.txt', 'r') as f:
            domains = f.read().splitlines()
    except FileNotFoundError:
        print("Error: domains-doh.txt not found.")
        sys.exit(1)

    print(f"Resolving {len(domains)} domains using concurrent threads...")

    all_ipv4 = set()
    all_ipv6 = set()

    # Use ThreadPoolExecutor to run tasks in parallel
    # Adjust max_workers based on your system (20-50 is usually safe for network tasks)
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        # Submit all domains to the executor
        future_to_domain = {executor.submit(resolve_domain, domain): domain for domain in domains}

        # Process results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_domain)):
            domain = future_to_domain[future]
            try:
                data = future.result()
                all_ipv4.update(data['A'])
                all_ipv6.update(data['AAAA'])
            except Exception as exc:
                print(f'{domain} generated an exception: {exc}')

            # Optional: Print progress every 50 domains
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{len(domains)} domains...")

    # Write results to files
    print("Writing results to files...")
    with open('ipv4-doh.txt', 'w') as ipv4_file:
        ipv4_file.write("\n".join(sorted(all_ipv4)) + "\n")

    with open('ipv6-doh.txt', 'w') as ipv6_file:
        ipv6_file.write("\n".join(sorted(all_ipv6)) + "\n")

    print("Resolution complete.")

if __name__ == "__main__":
    main()