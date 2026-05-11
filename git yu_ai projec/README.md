## Yu AI Project
    This project automatically scrapes and updates data from the Yarmouk University website,
    including FAQs, announcements, and general The data is converted into embeddings and used for retrieval-augmented generation (RAG) to answer user queries using ai generated response to be as helpful as possible.
    The system supports multiple configurable AI agents, each with different rules, models, and data sources.
Table of Contents
    1. [Configuration](#configuration)
    2. [Usage](#usage)
    3. [Contributing](#contributing)

## Configuration

There are **two configuration files** you will work with:

1. **`ai_agent_creator.json`**  
   - This is the brain of the system.  
   - You can create a new AI agent with custom rules and files it gets its information from.

2. **`websites_files_config.json`**  
   - This file controls the scraper and embedding system.  
   - You can create a custom version for another AI agent, **but the structure must remain the same**.



**`ai_agent_creator.json`**
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

- Users can **copy this JSON directly** into a file without causing errors.  


### Explanation of `ai_agent_creator.json` keys

- **`activation`**: Should this agent be active? `true` or `false`.
- **`websites_files_config`**: Links to the scraper and embedding system.
- **`minimum_key_similarity`**: Threshold for keyword search before full search fallback.
- **`general_embedding_file`**: Embedding file used if threshold is not reached.
- **`rules_files`**: Language-specific rules (`ar` for Arabic, `en` for English) this can take more than two language if you want add more.
- **`ai_model`**: Model the agent uses for conversation.
- **`embedding_model`**: Model used for creating embeddings.
- **`temperature`**: Creativity/variability of the agent (0 = strict, 0.5 = balanced, 1 = very creative).
- **`number_of_copies`**: How many concurrent users this agent can serve.
### end

**`websites_files_config.json`** 
```json
{  
    "https://www.yu.edu.jo/index.php/ann-ar?limit=0&start=0": {
    "update_embedd": true,
    "crawler_file_filter": [ "ann-ar/" ],
    "update": true,
    "type": "CR",
    "file": "real_time_information/annucments_arabic.json"
  }
}
```
### Explanation of `websites_files_config.json` keys
**'update_embedd'**: If true, the system updates the embeddings for this file when you run update_file.py.

**'update'**: If true, the scraper will fetch new data from the website automatically.

**'type'**: Type of scraper used. Different types may require different scraping methods and file formats.

**'includes several keys'**.

    1-"FAQ" Frequently asked question website format

    2-"PO" paragraphs only format
            
    5-"CR" crawling websites in the website

**'crawler_file_filter'**: a special list you add Filters the content the crawler will save. Only files matching these patterns are stored and there is no need to add this if the ttyoe is not "CR"
**'example'** :
    -crawler_file_filter:[".pdf"]
    -that will only take pdf files 

**'file'**: Path where the scraped data will be saved.

## Usage

### how to start the server
1. Development Mode

    Run the app normally for testing:
    ```bash
    python app.py
    ```
    Then open the website in your browser.
2. Production Mode

    For production, use Waitress (more stable and secure):
    
    ```bash
    waitress-serve --host=0.0.0.0 --port=5000 app:app
    ```
    host=0.0.0.0 allows access from any device

    port=5000 is the default port used by the app

### Updating Data
to update the stored information:

**Update**

    Run:
    ```bash
    py -3.10 manual_update.py
    ```
This updates all allowed entries in websites_files_config.json.

## Contributors

This project was created by Ahmad Najdat Turani.

Contributions are welcome!
If you’d like to improve the project, feel free to submit changes or suggestions.