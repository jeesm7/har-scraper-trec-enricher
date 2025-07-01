import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import re
from tqdm import tqdm

BASE_URL = "https://www.har.com/austin/real_estate_agents?officecity=dallas&search_type=member&seo=1&sort=rnd&page_size=20&page={page}"
TOTAL_PAGES = 144  # All pages

def get_city_name_from_url(url):
    """Extract city name from the BASE_URL for the CSV filename"""
    # Extract from the path part: /dallas/real_estate_agents
    match = re.search(r'/([^/]+)/real_estate_agents', url)
    if match:
        city = match.group(1)
        # Convert to proper format for filename
        city = city.replace('-', '_')
        return city
    return "unknown_city"

# Automatically generate CSV filename based on city in URL
CITY_NAME = get_city_name_from_url(BASE_URL)
OUTPUT_CSV = f"har_{CITY_NAME}_agents1.csv"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_agent_data_from_page(soup):
    agents = []
    # Each agent is in a div with class 'agent-card'
    agent_blocks = soup.find_all('div', class_='agent-card')
    
    for block in agent_blocks:
        agent = {
            'name': '',
            'phone': '',
            'organization': '',
            'for_sale': '0',
            'for_rent': '0',
            'sold': '0',
            'leased': '0',
            'showings': '0'
        }
        
        # Extract name
        name_elem = block.find('a', class_='agent_signature--square__info__agent_name')
        if name_elem:
            agent['name'] = name_elem.get_text(strip=True)
        
        # Extract phone number
        phone_elem = block.find('a', class_='view-phone')
        if phone_elem and phone_elem.has_attr('data-phone'):
            agent['phone'] = phone_elem['data-phone']
        else:
            # Fallback: look for agent-phone element (some might not be hidden)
            phone_elem = block.find('a', class_='agent-phone')
            if phone_elem:
                agent['phone'] = phone_elem.get_text(strip=True)
        
        # Extract organization/company from broker_name section
        broker_section = block.find('div', class_='agent_signature--square__info__broker_name')
        if broker_section:
            address_elem = broker_section.find('a', class_='text-wrap')
            if address_elem:
                agent['organization'] = address_elem.get_text(strip=True)
        
        # Extract property statistics
        stats_container = block.find('div', class_='d-flex pt-1 flex-wrap')
        if stats_container:
            # Find all stat links within the container
            stat_links = stats_container.find_all('a', class_='pr-4')
            for link in stat_links:
                span = link.find('span', class_='font_weight--bold')
                if span:
                    number = span.get_text(strip=True)
                    text = link.get_text(strip=True)
                    
                    # Extract the stat type and assign to appropriate field
                    if 'For Sale' in text:
                        agent['for_sale'] = number
                    elif 'For Rent' in text:
                        agent['for_rent'] = number
                    elif 'Sold' in text:
                        agent['sold'] = number
                    elif 'Leased' in text:
                        agent['leased'] = number
                    elif 'Showings' in text:
                        agent['showings'] = number
        
        # Only add agent if we found at least a name
        if agent['name']:
            agents.append(agent)
    
    return agents

def main():
    print(f"Starting scraper for {CITY_NAME.upper()}")
    print(f"Output file: {OUTPUT_CSV}")
    
    # Clear the CSV file and write header
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'phone', 'organization', 'for_sale', 'for_rent', 'sold', 'leased', 'showings']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    total_agents = 0
    for page in tqdm(range(1, TOTAL_PAGES + 1)):
        url = BASE_URL.format(page=page)
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Failed to fetch page {page}, status: {resp.status_code}")
            continue
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        agents = get_agent_data_from_page(soup)
        
        # Save agents from this page immediately
        with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'phone', 'organization', 'for_sale', 'for_rent', 'sold', 'leased', 'showings']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for agent in agents:
                writer.writerow(agent)
        
        total_agents += len(agents)
        print(f"Page {page}: Found {len(agents)} agents (Total so far: {total_agents})")
        
        # Be polite to the server
        time.sleep(1)
    
    print(f"Scraping complete! Found {total_agents} agents total.")
    print(f"Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main() 