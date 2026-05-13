import file_update
import json
import website_scraper
with open("ai_agent_creator.json", "r", encoding="utf-8") as f:
    ai_agents_data = json.load(f)
for agent, agent_data in ai_agents_data.items():
    all_ar_files_info = []
    all_eng_files_info = []
    with open(agent_data["websites_files_config"], "r", encoding="utf-8") as cfg:
            website_files_config = json.load(cfg)
    scraper = website_scraper.WebsiteScraper(website_files_config)
    for url, file_data in scraper.website_files_config.items():
        if url == "general_config":
            continue
        print(url)
        should_update_info = (file_data.get("update_info", True) or scraper.FORCE_UPDATE_ALL) and not scraper.FORCE_STOPE_UPDATE_ALL
        if not should_update_info:
            print(f"Skipping (Update Disabled): {url}")
            continue
        scraper.save_into_file(url,file_data)
    embedder = file_update.FileUpdate(agent_data, website_files_config)
    for url, file_data in scraper.website_files_config.items():
        if url == "general_config":
            continue
        print(url)
        should_update_embedd = (file_data.get("update_embedd", True) or embedder.FORCE_UPDATE_ALL) and not embedder.FORCE_STOP_UPDATE_ALL
        if not should_update_embedd:
            print(f"Skipping (Update embedding Disabled): {url}")
            continue
        info = embedder.save_file(file_data)
        if file_data.get("language") == "ar":
            all_ar_files_info.extend(info)
        else:
            all_eng_files_info.extend(info)
    with open(agent_data["general_embedding_files"]["ar"], "w", encoding="utf-8") as json_file:
        json.dump(all_ar_files_info, json_file)
    with open(agent_data["general_embedding_files"]["en"], "w", encoding="utf-8") as json_file:
        json.dump(all_eng_files_info, json_file)