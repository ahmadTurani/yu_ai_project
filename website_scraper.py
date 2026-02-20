import requests as rq
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        label = a.get_text(strip=True)
        href = urljoin(base_url, a["href"])

        if not label:
            continue

        links.append({
            "type": "link",
            "label": label,
            "from_page": base_url,
            "to_page": href
        })
    return links
def detect_location(tag):
    for parent in tag.parents:
        if parent.name in ["nav", "header"]:
            return "header_navigation"
        if parent.name == "footer":
            return "footer"
        if parent.name == "main":
            return "main_content"
    return "unknown"

def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; YuAI/1.0)"}

    response = rq.get(url, headers = headers, timeout=10)
    response.raise_for_status()
    return response.text
def chunk(text):
    lines = text.split(".")
    return "\\n".join(lines)
            
                
        
        
def extract_FAQ(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer"]):
        tag.decompose()

    chunks = []
    panels = soup.select(".sppb-panel")

    for panel in panels:
        title_tag = panel.select_one(".sppb-panel-title")
        body_tag = panel.select_one(".sppb-panel-body")

        if not title_tag or not body_tag:
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
                "type": "common_information",
                "title": title,
                "content": content,
                "relevant_urls": relevant_urls,
                "source": base_url
            })

    return chunks

def extract_MW(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # remove noise
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer"]):
        tag.decompose()
    
    chunks = []
    current_title = None
    current_content = []
    relevant_urls = {}

    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        if tag.name in ["h1", "h2", "h3"]:
            if current_title and current_content:
                chunks.append({
                    "type": "content_chunk",
                    "title": current_title,
                    "content":current_content,
                    "relevant_urls": relevant_urls,
                    "source": base_url
                })

            current_title = tag.get_text(strip=True)
            current_content = []
            relevant_urls = {}
        else:
            for a in tag.find_all("a", href=True):
                anchor_text = a.get_text(strip=True)
                relevant_urls[anchor_text] = urljoin(base_url, a["href"])
                a.replace_with(anchor_text)  # Keep anchor text in content
            text = tag.get_text(" ", strip=True)
            if len(text) > 30:
                current_content.append(text)

    # save last chunk
    if current_title and current_content:
        chunks.append({
            "type": "content_chunk",
            "title": current_title,
            "content": " ".join(current_content),
            "relevant_urls": relevant_urls,
            "source": base_url
        })

    return chunks
def extract_news_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    news = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = urljoin(base_url, a["href"])

        if not title or len(title) < 10:
            continue

        # basic filter for news URLs
        if "news" in href or "article" in href:
            news.append({
                "title": title,
                "url": href
            })

    return news
def extract_article(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav"]):
        tag.decompose()

    # Article title
    title_tag = soup.find(["h1", "h2"])
    title = title_tag.get_text(strip=True) if title_tag else "Untitled"

    # Noise filter
    commone_noise = [
        "Jobs | Scholarships | Students | Staff | Alumni",
        "Irbid - Jordan, P.O Box 566 ZipCode 21163",
        "طلبات القبول الطلبة الدوليين طلبات الموازي طلبات الدراسات العليا طلبات الدبلوم استكمال إجراءات القبول الموحد"        
    ]

    content = []
    relevant_urls = {}

    for tag in soup.find_all(["p", "li"]):
        # Extract URLs
        for a in tag.find_all("a", href=True):
            anchor_text = a.get_text(strip=True)
            relevant_urls[anchor_text] = urljoin(base_url, a["href"])
            a.replace_with(anchor_text)

        text = tag.get_text(" ", strip=True)
        if len(text) < 30:
            continue
        if text in commone_noise:
            continue
        content.append(text)

    return {
        "type": "news_article",
        "title": title,
        "content": "\n".join(content),
        "relevant_urls": relevant_urls,
        "source": base_url,
        "language": "en" if title.isascii() else "ar"
    }

def crawl_news_page(news_list_url):
    html = fetch_html(news_list_url)

    news_links = extract_news_links(html, news_list_url)

    articles = []

    for item in news_links:
        try:
            print("Fetching:", item["url"])
            article_html = fetch_html(item["url"])
            article = extract_article(article_html, item["url"])
            articles.append(article)
        except Exception as e:
            print("Skipped:", item["url"], e)

    return articles

def orgnized_text(url):
    if url == "https://www.yu.edu.jo/index.php/en/faq-en" or url == "https://www.yu.edu.jo/index.php/faq-ar":
        orgnized_text = extract_FAQ(fetch_html(url), url)
    elif url == "https://www.yu.edu.jo/index.php/en/" or url == "https://www.yu.edu.jo/index.php/ar/":
        orgnized_text = extract_MW(fetch_html(url), url)
    elif url == "https://www.yu.edu.jo/index.php/en/ann-en" or url == "https://www.yu.edu.jo/index.php/ann-ar":
        orgnized_text = extract_FAQ(fetch_html(url), url)
    elif url == "https://www.yu.edu.jo/index.php/en/home-portfolio/yu-news" or url == "https://www.yu.edu.jo/index.php/newsevents/yu-news-ar":
        orgnized_text = crawl_news_page(url)
    else :
        orgnized_text = extract_MW(fetch_html(url), url)
    return orgnized_text

def save_into_file():
    websites_files_config =open("websites_files_config.json","r",encoding= "utf-8")
    websites_files = json.load(websites_files_config)
    websites_files_config.close
    for url, file_path in websites_files.items():
        print(url)
        with open(file_path, 'w') as json_file:
            json.dump(orgnized_text(url), json_file, ensure_ascii=False, indent = 2)

save_into_file()


