import json
import requests

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
                                    results[record_type].add(f"{answer['data']} #{domain}")  # Add to set
                            else:
                                print(f"Unexpected answer format for {domain} from {server['name']}: {answer}")
                    else:
                        print(f"No answers found for {domain} with {server['name']}: {data}")

                else:
                    print(f"Unexpected response status {response.status_code} for {domain} with {server['name']}")

            except requests.RequestException as e:
                print(f"Error resolving {domain} with {server['name']}: {e}")
            except Exception as e:
                print(f"Error processing domain {domain}: {e}")

    return results

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