import json
import website_scraper
import ollama
class FileUpdate ():
    def __init__(self, agent_data, websites_files_config):
        self.general_embedding_files = agent_data["general_embedding_files"]
        self.embedding_model = agent_data["embedding_model"]
        self.websites_files_config = websites_files_config
        self.FORCE_UPDATE_ALL= websites_files_config["general_config"]["FORCE_UPDATE_EMBEDD_ALL"]
        self.FORCE_STOP_UPDATE_ALL= websites_files_config["general_config"]["FORCE_STOP_UPDATE_EMBEDD_ALL"]

    def embeddings_extractor(self, file):
        with open(file, "r", encoding="utf-8") as file_info:
            infos = json.load(file_info)
        embeddings = []
        count = 0
        for info in infos :
             count += 1
             print(f"paragraph{count} embeded")
             print(len(info["content"]))
             response = ollama.embed(
                 model=self.embedding_model,
                 input=info["content"])

             embeddings.append({
                 "embedding": response.embeddings,
                 "text": info["content"],
                 "title": info["title"],
                 "source": info["source"],
                 "relevant_urls": info["relevant_urls"]
                 })
        return embeddings
    def embeddings_extractor_if_LE(self, file):
        with open(file, "r", encoding="utf-8") as file_info:
            links = json.load(file_info)
        embeddings = []
        count = 0
        for link in links :
             count += 1
             print(f"link_chain{count} embeded")
             print(len(info["content"]))
             response = ollama.embed(
                 model=self.embedding_model,
                 input=info["content"])

             embeddings.append({
                 "embedding": response.embeddings,
                 "text": info["content"],
                 "title": info["title"],
                 "source": info["source"],
                 "relevant_urls": info["relevant_urls"]
                 })
        return embeddings
    def save_file(self,data):
        info = self.embeddings_extractor(data["file"])
        new_file = data["file"].replace(".json","_embedded.json")
        with open(new_file, "w", encoding="utf-8") as json_file:
            json.dump(info, json_file)
        print(data["file"], ": embedded")
        return info





