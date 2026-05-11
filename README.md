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
