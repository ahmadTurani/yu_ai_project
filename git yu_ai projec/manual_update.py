import file_update
import json
import website_scraper
with open("ai_agent_creator.json", "r", encoding="utf-8") as f:
    ai_agents_data = json.load(f)
for agent, agent_data in ai_agents_data.items():
    all_files_info = []
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

    for url, file_data in scraper.website_files_config.items():
        embedder = file_update.FileUpdate(agent_data, website_files_config)
        if url == "general_config":
            continue
        print(url)
        should_update_embedd = (file_data.get("update_embedd", True) or embedder.FORCE_UPDATE_ALL) and not embedder.FORCE_STOP_UPDATE_ALL
        if not should_update_embedd:
            print(f"Skipping (Update embedding Disabled): {url}")
            continue
        info = embedder.save_file(file_data)
        all_files_info.extend(info)
    with open(embedder.general_embedding_file, "w", encoding="utf-8") as f:
        json.dump(all_files_info, f)
