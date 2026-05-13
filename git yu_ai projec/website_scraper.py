from dataclasses import dataclass
import requests as rq
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
from bidi.algorithm import PARAGRAPH_LEVELS, get_display
from requests.sessions import should_bypass_proxies
import file_extractor
import logging

logging.basicConfig(level=logging.INFO, filename="info.log")
class WebsiteScraper():
    def __init__(self,website_files_config, FORCE_UPDATE_ALL = False, FORCE_STOPE_UPDATE_ALL = False):
        self.website_files_config = website_files_config 
        self.FORCE_UPDATE_ALL = self.website_files_config["general_config"]["FORCE_UPDATE_INFO_ALL"]
        self.FORCE_STOPE_UPDATE_ALL = self.website_files_config["general_config"]["FORCE_STOP_UPDATE_INFO_ALL"]
        self.visited_urls = set()
    def detect_site_type(self,html,url):
        if html :
            soup = BeautifulSoup(html, "html.parser")
        else :
            return "PO"
        if url.endswith(".pdf"):
            return "PDF"
        if soup.select(".sppb-panel") or soup.select(".accordion"):
            return "FAQ"
        return "PO"

    def extract_links(self, html, base_url, crawler_file_filter):
        if html is None or html == "":
            print(f"Skipping BeautifulSoup: No HTML content for {base_url}")
            return []
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            href = urljoin(base_url, a["href"])

            if not crawler_file_filter:
                crawler_file_filter = [""]
            if not href:
                href = ""
            if any(substring.lower() in href.lower() for substring in crawler_file_filter) and ( "http"  in href or "https" in href):
                links.append({
                "title": title,
                "url": href
                })
        print(f"Extracted {len(links)} links from {base_url}")
        return links
    
    def fetch_html(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; YuAI/1.0)"}
        try:
            response = rq.get(url, headers = headers, timeout=20)
            response.encoding = 'utf-8'
            response.raise_for_status()
        except rq.HTTPError as e:
            print(f"HTTP Error for {url}: {e}")
            return ""
        except rq.exceptions.ReadTimeout: 
            print(f"Timeout on {url}")
            return ""
        except rq.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return ""
        return response.text

    def extract_FAQ(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        page_number = {}


        # Remove noise
        for tag in soup(["script", "style", "noscript", "iframe", "header", "footer"]):
            tag.decompose()

        chunks = []
        panels = soup.select(".sppb-panel")

        for panel in panels:
            title_tag = panel.select_one(".sppb-panel-title")
            body_tag = panel.select_one(".sppb-panel-body")

            if not title_tag or not body_tag:
                title = "known"
                continue

            title = title_tag.get_text(strip=True)
            relevant_urls = {}
            # Extract and replace links
            for a in body_tag.find_all("a", href=True):
                anchor_text = a.get_text(strip=True)
                relevant_urls[anchor_text] = urljoin(base_url, a["href"])
                a.replace_with(anchor_text)  # Keep anchor text in content

            content = body_tag.get_text(" ", strip=True)
            if content:
                chunks.append({
                    "title": title,
                    "content": content,
                    "page_number": page_number,
                    "relevant_urls": relevant_urls,
                    "source": base_url
                })

        return chunks

    def extract_MW(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        # Remove noise
        for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav"]):
            tag.decompose()
    
        chunks = []
        current_title = "General Information" # Default title if page starts with <p>
        current_content = []
        current_urls = {} # Store URLs for the CURRENT section only

        # We iterate through all relevant tags
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li", "div"]):
            # If we hit a heading, save the previous chunk and reset
            if tag.name in ["h1", "h2", "h3"]:
                if current_content:
                    chunks.append({
                        "title": current_title,
                        "content": " ".join(current_content),
                        "page_number": {},
                        "relevant_urls": current_urls,
                        "source": base_url
                    })
            
                # Reset for the new section
                current_title = tag.get_text(strip=True)
                current_content = []
                current_urls = {} # IMPORTANT: Reset the dictionary here!
            
            else:
                # Check for links specifically inside this tag (p, li, or div)
                for a in tag.find_all("a", href=True):
                    anchor_text = a.get_text(strip=True)
                    if anchor_text: # Don't save empty anchors
                        current_urls[anchor_text] = urljoin(base_url, a["href"])
                
                    # We replace the link with text so the 'content' remains readable
                    a.replace_with(anchor_text)

                text = tag.get_text(" ", strip=True)
                # Apply your length filter
                if len(text) > 50:
                    current_content.append(text)

        # Save the very last chunk after the loop finishes
        if current_content:
            chunks.append({
                "title": current_title,
                "content": " ".join(current_content),
                "page_number": {},
                "relevant_urls": current_urls,
                "source": base_url
            })

        return chunks

    def extract_important_text_only(self, html, base_url):
        if not html:
            return []
        relevant_urls = {}
        paragraphs = []
        chunks =[]
        noise = ["Jobs | Scholarships | Students | Staff | Alumni", "وظائف | بعثات | الطلبة | العاملون | الخريجون"]
        seen = set()
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav"]):
            tag.decompose()
        title_tag = soup.find("h2", {"itemprop": "name"})
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"
        for p in soup.find_all("p"):
        #We check for links specifically inside this tag (p)
            for img in p.find_all("img", src=True):
                img.decompose()


            for a in p.find_all("a", href=True):
                anchor_text = a.get_text(strip=True)
                if anchor_text: # Only map if there is actual text
                    link = urljoin(base_url, a["href"])
                    relevant_urls[anchor_text] = link
                    # Replace the link tag with its text so get_text() sees just the word
                    a.replace_with(anchor_text)

            line = p.get_text(" ", strip=True)
            if line and line not in seen and line not in noise:
                paragraphs.append(line)
                seen.add(line)
        text = "\n\n".join(paragraphs)
        if text:
            chunks.append({
            "title": title,
            "content": text,
            "page_number": 0,
            "relevant_urls": relevant_urls,
            "source": base_url
        })
        return chunks

    def extract_links_and_info(self, html, base_url, crawler_file_filter):
        links = self.extract_links(html, base_url, crawler_file_filter)
        text = []
        for link in links:
            text.extend(self.orgnized_text(link["url"]))
            print (link["url"], " loaded")
        return text

    def orgnized_text(self, url, Type = None, lang = None, crawler_file_filter = [], depth = 0):
        if url in self.visited_urls:
            return []
        self.visited_urls.add(url)

        if not Type:
            Type = self.detect_site_type(self.fetch_html(url),url)
        if Type == "FAQ":
            orgnized_text = self.extract_FAQ(self.fetch_html(url), url)
        elif Type == "CR":
            orgnized_text = self.extract_links_and_info(self.fetch_html(url), url, crawler_file_filter)

        elif Type == "pdf":
            response = rq.get(url, timeout=20)
            temp_filename = "temp_processing.pdf"
            with open(temp_filename, "wb") as f:
                f.write(response.content)
            orgnized_text = file_extractor.process_pdf(temp_filename, url)
        else:
            orgnized_text = self.extract_important_text_only(self.fetch_html(url), url)

        if orgnized_text is None:
            orgnized_text = []
        

        return orgnized_text

    def save_into_file(self,url,file_data):
        with open(file_data["file"], 'w', encoding='utf-8') as json_file:
            json.dump(self.orgnized_text(url, file_data["type"], file_data.get("lang"), file_data.get("crawler_file_filter"), file_data.get("depth")), json_file, ensure_ascii=False, indent = 2)