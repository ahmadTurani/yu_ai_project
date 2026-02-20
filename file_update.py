import ollama
import json
import website_scraper

with open("ai_agent_creator.json", "r", encoding="utf-8") as f:
    ai_agents_data = json.load(f)
class FileUpdate ():
    def __init__(self, key_words_to_files = "key_words_to_files.json"):
        self.key_words_to_files = key_words_to_files
        keywords_to_file = open(self.key_words_to_files,"r", encoding="utf-8")
        self.keywords = json.load(keywords_to_file)
        keywords_to_file.close()
    def embeddings_extractor(self):
        embeddings = []
        for key, file_path in self.keywords.items():
            print("keywords loaded:", self.keywords)
            print("Checking file:", file_path)
            if file_path.endswith(".json"):
                file = open(file_path,"r", encoding="utf-8")
                infos = json.load(file)
                file.close()
                count = 0
                for info in infos :
                    if isinstance(info["content"], str):
                        count += 1
                        lines = []
                        print(f"paragraph{count} embeded")
                        lines.append("type:" + info["type"])
                        lines.append("title:" + info["title"])
                        lines.append("content:" + info["content"])
                        lines.append("source:" + info["source"])
                        lines.append("relevant_urls" + str(info["relevant_urls"]))
                        new_info = "\n".join(lines)
                        response = ollama.embed(
                            model="qwen3-embedding",
                            input=new_info
                            
                            )
                        embeddings.append({
                            "embedding": response.embeddings,
                            "text": new_info,
                            "type": info["type"],
                            "title": info["title"],
                            "source": info["source"],
                            "relevant_urls": info["relevant_urls"]
                            })
                    else:
                        for paragraph in info["content"]:
                            count += 1
                            lines = []
                            print(f"paragraph{count} embeded")
                            lines.append("type:" + info["type"])
                            lines.append("title:" + info["title"])
                            lines.append("content:" + paragraph)
                            lines.append("source:" + info["source"])
                            lines.append("relevant_urls" + str(info["relevant_urls"]))
                            new_info = "\n".join(lines)
                            response = ollama.embed(
                                model="qwen3-embedding",
                                input=new_info
                                )
                            embeddings.append({
                                "embedding": response.embeddings,
                                "text": new_info,
                                "type": info["type"],
                                "title": info["title"],
                                "source": info["source"],
                                "relevant_urls": info["relevant_urls"]

                                })
        return embeddings
    def save_file(self):
        website_scraper.save_into_file()
        json_file = open("embedding_file.json","w", encoding="utf-8")
        json.dump(self.embeddings_extractor(), json_file)
        json_file.close()
files = FileUpdate()
files.save_file()