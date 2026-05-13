# 🎓 Yu AI — Yarmouk University AI Assistant

A fully local, privacy-preserving RAG (Retrieval-Augmented Generation) system built for Yarmouk University. It scrapes live data from the university website, embeds it using local models, and answers student queries in **Arabic and English** — with zero hallucination, zero API keys, and zero data leaving your server.

---

## ✨ Features

- 🌐 **Live data scraping** — automatically pulls FAQs, announcements, and news from 8+ sources
- 🔍 **FAISS vector search** — fast semantic search across embedded university data
- 🤖 **Local LLM** — runs entirely on your machine, no cloud required
- 🌍 **Bilingual** — full Arabic and English support with language detection
- ⚙️ **Multi-agent config** — define multiple AI agents with different rules, models, and data sources
- 🔒 **Privacy first** — no data sent to any external service

---

## 🏗️ Architecture

```
University Website
       │
       ▼
  BeautifulSoup Scraper
  (FAQs, News, Announcements)
       │
       ▼
  Ollama Embeddings
  (qwen3-embedding)
       │
       ▼
   FAISS Index
  (Vector Search)
       │
  User Question ──► Embed Query ──► Search Index ──► Retrieve Chunks
                                                            │
                                                            ▼
                                                     Qwen2.5 7B (Local LLM)
                                                            │
                                                            ▼
                                                     Answer in Arabic/English
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Web Scraping | BeautifulSoup |
| Embeddings | Ollama + qwen3-embedding |
| Vector Search | FAISS |
| Local LLM | Qwen2.5 7B (via Ollama) |
| Language Detection | langid |
| API Server | Flask |
| Production Server | Waitress |

---

## 📁 Project Structure

```
yu-ai/
├── app.py                          # Flask API server
├── manual_update.py                # Script to update scraped data
├── ai_agent_creator.json           # Agent configuration
├── websites_files_config.json      # Scraper & embedding config
├── rules_ar.txt                    # Arabic agent rules/prompt
├── rules_en.txt                    # English agent rules/prompt
└── real_time_information/          # Scraped & embedded data
    ├── questions.json
    ├── questions_arabic.json
    ├── announcements.json
    └── ...
```

---

## ⚙️ Configuration

There are **two configuration files**:

### 1. `ai_agent_creator.json` — Agent Configuration

```json
{
    "agent1": {
        "activation": true,
        "websites_files_config": "websites_files_config.json",
        "general_embedding_file": "embedding_file.json",
        "rules_files": {
            "ar": "rules_ar.txt",
            "en": "rules_en.txt"
        },
        "ai_model": "qwen2.5:7b",
        "embedding_model": "qwen3-embedding",
        "temperature": 0.5,
        "number_of_copies": 1
    }
}
```

| Key | Description |
|-----|-------------|
| `activation` | Enable or disable this agent |
| `websites_files_config` | Path to the scraper config file |
| `general_embedding_file` | Fallback embedding file |
| `rules_files` | Language-specific system prompt files |
| `ai_model` | Ollama model used for answering |
| `embedding_model` | Ollama model used for embeddings |
| `temperature` | 0 = strict, 0.5 = balanced, 1 = creative |
| `number_of_copies` | Concurrent users this agent can serve |

---

### 2. `websites_files_config.json` — Scraper Configuration

```json
{
    "https://www.yu.edu.jo/index.php/faq-ar": {
        "update_embedd": true,
        "update_info": true,
        "type": "FAQ",
        "file": "real_time_information/questions_arabic.json",
        "language": "ar"
    }
}
```

| Key | Description |
|-----|-------------|
| `update_embedd` | Re-embed this source on next update |
| `update_info` | Re-scrape this source on next update |
| `type` | Scraper type: `FAQ`, `CR` (crawler), or `PO` (paragraphs only) |
| `file` | Path to save scraped data |
| `language` | Language of the source (`ar` or `en`) |
| `crawler_file_filter` | *(CR type only)* Only store URLs matching these patterns |

**Scraper types:**
- `FAQ` — Frequently Asked Questions page format
- `CR` — Full website crawler with optional URL filtering
- `PO` — Paragraphs only format

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- Required models pulled:
```bash
ollama pull qwen2.5:7b
ollama pull qwen3-embedding
```

### Installation

```bash
git clone https://github.com/yourusername/yu-ai.git
cd yu-ai
pip install -r requirements.txt
```

### Scrape & Embed Data

```bash
python manual_update.py
```

This scrapes all sources marked `update_info: true` and re-embeds all sources marked `update_embedd: true`.

### Run the Server

**Development:**
```bash
python app.py
```

**Production:**
```bash
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

---

## 🔧 Adding a New Data Source

1. Open `websites_files_config.json`
2. Add a new entry:
```json
"https://yoursite.com/page": {
    "update_embedd": true,
    "update_info": true,
    "type": "FAQ",
    "file": "real_time_information/your_file.json",
    "language": "en"
}
```
3. Run `python manual_update.py`

That's it — the new source is scraped, embedded, and searchable.

---

## 🌍 Adapting for Another University or Organization

This project is built as a **reusable RAG framework**. To adapt it:

1. Replace the URLs in `websites_files_config.json` with your organization's pages
2. Update the rules in `rules_ar.txt` and `rules_en.txt` with your own system prompt
3. Run `manual_update.py` to scrape and embed your data
4. Start the server

No code changes needed.

---

## 👤 Author

**Ahmad Najdat Turani**  
Computer Science Student — Yarmouk University  

Contributions are welcome — feel free to open an issue or submit a pull request.
