import dns.resolver  # 02-subdomain
import requests  # 03-status/title
from bs4 import BeautifulSoup
import socket  # 04-ip and 05-port
import re  # regex
import whois  # 07-whois
import argparse  # 08-args
import os  # for handling file paths

# pip install beautifulsoup4
from bs4 import BeautifulSoup

# pip install requests
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(current_dir, 'template.html')

with open(template_path, "r", encoding="utf-8") as file:
    template = file.read()

def get_links(url):
    # Send a GET request to the URL
    try:
        response = requests.get(url)
    except:
        return []
    
    # Parse the HTML response using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all the links on the page
    links = []
    for link in soup.find_all("a"):
        href = link.get("href")
        
        # Ignore links that are not URLs
        if href is not None and href.startswith("http"):
            links.append(href)
            
    return links

def crawl_site(url, depth=2):
    # Dictionary to store the site map
    site_map = {}
    
    # Recursive function to crawl the site and generate the sitemap
    def crawl(url, current_depth):
        # Stop crawling if we have reached the maximum depth specified
        if current_depth > depth:
            return
        
        # Get all the links on the current page
        links = get_links(url)
        
        # Add the links to the site map
        site_map[url] = links
        
        # Crawl each link recursively
        for link in links:
            if link not in site_map:
                crawl(link, current_depth + 1)
    
    # Call the crawl function to generate the site map
    crawl(url, 0)
    
    return site_map

# Example usage: Generate a site map for http://example.com with a maximum depth of 2
site_map = crawl_site("https://www.rajanews.com/", depth=2)

sitemapHtml = "<ul>"
# Print the site map
for url, links in site_map.items():
    sitemapHtml += f"<li>{url}</li>"
    sublinks = "<ul>"
    for link in links:
        sublinks += f"<li>{link}</li>"
    sublinks += "</ul>"
    sitemapHtml += sublinks;
sitemapHtml += "</ul>"
template = template.replace("$$Sitemap$$", sitemapHtml)

# 02-subdomain
domain = "paydarsamane.com"
subDomains = "<ul>"
try:
    ns = dns.resolver.resolve(domain, 'NS')
    for server in ns:
        server = str(server)
        subdomain = "api"
        try:
            answers = dns.resolver.resolve(subdomain + "." + domain, "A")
            for ip in answers:
                subDomains += f"<li>{subdomain}.{domain} - {ip}</li>"
        except:
            pass
except Exception as e:
    subDomains += f"<li>Error: {str(e)}</li>"
subDomains += "</ul>"
template = template.replace("$$SubDomains$$", subDomains)

# 03-status / title and 06-regex
url = "https://paydarsamane.com/blog/category/programming"
# url = "https://www.rajanews.com/%D8%AA%D9%85%D8%A7%D8%B3"
response = requests.get(url)
Status = "Success"
if response.status_code == 200:
    text = response.text
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    phonePattern = r"0\d{2}\b[- ]*\b\d{8}"
    # phonePattern = r"\b\d{8}[- ]*0\d{2}\b"
    email = re.search(pattern, text)
    phone = re.search(phonePattern, text)

    if email:
        template = template.replace("$$Email$$", email.group())
    else:
        template = template.replace("$$Email$$", "Not found")
    if phone:
        template = template.replace("$$Phone$$", phone.group())
    else:
        template = template.replace("$$Phone$$", "Not Found")

elif response.status_code == 404:
    Status = "404: Page not found"
elif response.status_code == 500:
    Status = "500: Internal server error."
else:
    Status = f"Unknown status code: {response.status_code}"

template = template.replace("$$Status$$", Status)

# 04-ip
try:
    ip_address = socket.gethostbyname(domain)
    template = template.replace("$$IP$$", ip_address)
except Exception as e:
    template = template.replace("$$IP$$", f"Error : {str(e)}")

# 05-port
ports = "<ul>"
ip = "185.188.104.10"
common_ports = [21, 22, 23, 25, 53, 80, 110, 119, 123, 143, 161, 194, 443, 445, 993, 995]
for port in common_ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((ip, port))
    if result == 0:
        ports += f"<li>{port}: open</li>"
    else:
        ports += f"<li>{port}: close</li>"
    sock.close()
ports += "</ul>"
template = template.replace("$$Ports$$", ports)

# 07-whois
whois_info = ""
try:
    w = whois.whois(domain)
    whois_info += f"""
    <p>Domain registrar: {w.registrar}</p>
    <p>WHOIS server: {w.whois_server}</p>
    <p>Domain creation date: {w.creation_date}</p>
    <p>Domain expiration date: {w.expiration_date}</p>
    <p>Domain last updated: {w.last_updated}</p>
    <p>Name servers: {', '.join(w.name_servers) if w.name_servers else 'N/A'}</p>
    <p>Registrant name: {w.name}</p>
    <p>Registrant organization: {w.org}</p>
    <p>Registrant email: {w.email}</p>
    <p>Registrant phone: {w.phone}</p>
    """
except Exception as e:
    whois_info += f"<p>Error: {str(e)}</p>"
template = template.replace("$$Whois$$", whois_info)

# 03-status / title
url = "https://paydarsamane.com"
# url = "https://rajanews.com"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
title = soup.title.string if soup.title else "No title found"
template = template.replace("$$Title$$", title)

# Save to HTML file
reconPath = os.path.join(current_dir, 'Recon.html')
with open(reconPath, "w", encoding="utf-8") as file:
    file.write(template)