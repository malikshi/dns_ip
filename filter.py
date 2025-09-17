import ipaddress
import requests
import sys

def fetch_and_parse_networks(url):
    """
    Fetches a list of networks from a URL, filters out comments and empty lines,
    and returns a list of valid ipaddress network objects.
    """
    try:
        response = requests.get(url)
        # Raise an exception for bad status codes (like 404 or 500)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return []

    networks = []
    for line in response.text.splitlines():
        # Remove leading/trailing whitespace
        line = line.strip()

        # Filter out empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Ensure the line is a valid network, skipping invalid lines
        try:
            networks.append(ipaddress.ip_network(line))
        except ValueError:
            print(f"Warning: Skipping invalid network entry '{line}' in {url}", file=sys.stderr)
            continue
    return networks

# --- Main Script ---

# Step 1: Fetch and parse network lists from URLs
print("Fetching and parsing exclusion lists...")
cloudflare_ipv4_url = "https://www.cloudflare.com/ips-v4"
cloudflare_ipv6_url = "https://www.cloudflare.com/ips-v6"
vercel_url = "https://raw.githubusercontent.com/malikshi/dns_ip/main/vercel.txt"
exclude_ips_url = "https://raw.githubusercontent.com/malikshi/dns_ip/main/exclude.txt"
fastly_url = "https://raw.githubusercontent.com/malikshi/geoip/refs/heads/release/text/fastly.txt"

all_exclusion_networks = (
    fetch_and_parse_networks(cloudflare_ipv4_url) +
    fetch_and_parse_networks(cloudflare_ipv6_url) +
    fetch_and_parse_networks(vercel_url) +
    fetch_and_parse_networks(fastly_url) +
    fetch_and_parse_networks(exclude_ips_url)
)

# Step 2: Read IP addresses from the local file
ip_dns_file = "ip-dns.txt"
try:
    with open(ip_dns_file, "r") as file:
        ip_dns_list = file.read().splitlines()
except FileNotFoundError:
    print(f"Error: Input file '{ip_dns_file}' not found. Please ensure it exists.", file=sys.stderr)
    sys.exit(1)

# Step 3-4: Filter the IP list by checking against the exclusion networks
print("Filtering IP addresses...")
filtered_ips = []
for ip_str in ip_dns_list:
    ip_str = ip_str.strip()
    # Skip empty lines in the source IP file as well
    if not ip_str:
        continue

    try:
        ip_addr = ipaddress.ip_address(ip_str)
    except ValueError:
        print(f"Warning: Skipping invalid IP address '{ip_str}' in {ip_dns_file}", file=sys.stderr)
        continue

    is_excluded = any(ip_addr in network for network in all_exclusion_networks)

    if not is_excluded:
        filtered_ips.append(ip_str)

# Step 5: Save the filtered list to the output files
output_with_prefix = "ip-dns-nocdn-prefix.txt"
output_without_prefix = "ip-dns-nocdn.txt"

print(f"Writing results to {output_with_prefix} and {output_without_prefix}...")

with open(output_with_prefix, "w") as file:
    for ip in filtered_ips:
        ip_addr = ipaddress.ip_address(ip)
        prefix = "/32" if ip_addr.version == 4 else "/128"
        file.write(f"{ip}{prefix}\n")

with open(output_without_prefix, "w") as file:
    for ip in filtered_ips:
        file.write(f"{ip}\n")

print(f"Filtering complete. {len(filtered_ips)} IPs have been saved.")