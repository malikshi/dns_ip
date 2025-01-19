import ipaddress
import requests

# Step 1: Fetch Cloudflare IPv4 and IPv6 networks
cloudflare_ipv4_url = "https://www.cloudflare.com/ips-v4"
cloudflare_ipv6_url = "https://www.cloudflare.com/ips-v6"
exclude_ips_url = "https://raw.githubusercontent.com/malikshi/dns_ip/main/exclude.txt"
cloudflare_ipv4_networks = requests.get(cloudflare_ipv4_url).text.splitlines()
cloudflare_ipv6_networks = requests.get(cloudflare_ipv6_url).text.splitlines()
exclude_ips_networks = requests.get(exclude_ips_url).text.splitlines()

# Step 2: Read IP addresses from the given URL
#ip_dns_url = "https://raw.githubusercontent.com/malikshi/dns_ip/main/ip-dns.txt"
ip_dns_file = "ip-dns.txt"
with open(ip_dns_file, "r") as file:
    ip_dns_list = file.read().splitlines()

# Step 3-4: Remove Cloudflare IP addresses from the list
filtered_ips = []
for ip in ip_dns_list:
    is_cloudflare_ip = False
    # for network in cloudflare_ipv4_networks + cloudflare_ipv6_networks + exclude_ips_networks:
    for network in exclude_ips_networks:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(network):
            is_cloudflare_ip = True
            break
    if not is_cloudflare_ip:
        filtered_ips.append(ip)

# Step 5: Save the modified list without Cloudflare IP addresses to a file
with open("ip-dns-nocdn-prefix.txt", "w") as file:
    for ip in filtered_ips:
        ip_with_prefix = ip + ("/32" if ipaddress.ip_address(ip).version == 4 else "/128")
        file.write(ip_with_prefix + "\n")

with open("ip-dns-nocdn.txt", "w") as file:
    for ip in filtered_ips:
        file.write(ip + "\n")

print("Filtered IP addresses without IPs Cloudflare.")
