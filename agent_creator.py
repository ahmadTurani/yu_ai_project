import ollama
import json
import numpy as np
import file_extractor
import langid

def detect_language(text):
    lang, confidence = langid.classify(text)
    return lang

class AiCreator:
    def __init__ (self, key_words_to_files, key_rules_file, rules_files, ai_model, embedding_file, temperature, num_predict = 50):
        self.key_words_to_files = key_words_to_files
        keywords_to_file = open(self.key_words_to_files,"r", encoding="utf-8")
        self.keywords = json.load(keywords_to_file)
        keywords_to_file.close()
        self.rules_files = rules_files
        self.key_rules_file = key_rules_file
        self.temperature = temperature
        self.num_predict = num_predict
        self.ai_model = ai_model
        f = open(embedding_file,"r", encoding="utf-8")
        self.embeddings = json.load(f)
        f.close()
        
    def embed_messages(self,message_content):
        response = ollama.embed(
            model="qwen3-embedding",
            input=message_content
            )
        embeddings = response.embeddings
        return embeddings

    def cosine_similarity(self, vec1, vec2):
        vec1 = np.array(vec1).flatten()
        vec2 = np.array(vec2).flatten()
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def find_relvant_info(self, message_content, number_of_retrievaled_info= 2):
        message_embedding = self.embed_messages(message_content)

        similarities = []

        for item in self.embeddings:
            score = self.cosine_similarity(message_embedding, item["embedding"])
            similarities.append((score, item["text"]))

        similarities.sort(reverse=True, key=lambda x: x[0])
        seen_texts = set()
        unique_similarities = []
        for score, text in similarities:
            if text not in seen_texts:
                unique_similarities.append((score, text))
                seen_texts.add(text)
        return unique_similarities[:number_of_retrievaled_info]
    def make_a_ai_respon(self,system_prompt,message_content):
        response = ollama.chat(model=self.ai_model, messages=[
            {   
                'role': 'system',
                'content': system_prompt 
                },
            {
                'role': 'user',
                'content': message_content ,
                },
                ],
            options={
                'temperature': self.temperature,
                "num_predict": self.num_predict
                })
        
        return response['message']['content']
    def build_keys_prompt(self):
        lines = ["المفاتيح المتاحة:"]
        for key in self.keywords.keys():
            lines.append(f"- {key}")
        return "\n".join(lines)
    def detect_keyword(self,message_content):
        rules_file = open(self.key_rules_file,"r", encoding="utf-8")
        rules = rules_file.read()
        rules_file.close()
        system_prompt = rules
        system_prompt += self.build_keys_prompt()
        self.temperature = 0.1
        self.num_predict = 1000
        key = self.make_a_ai_respon(system_prompt, message_content)
        print(key)
        key = key.strip()
        return key
    
    def load_file(self,file_path):
        if file_path.endswith(".txt"):
            file = open(file_path,"r", encoding="utf-8")
            info = file.read()
            file.close()
            print("loaded file = ", file_path)
            return info
        if file_path.endswith(".xlsx"):
            json_path = file_path.replace(".xlsx", ".json")
            json_file = open(json_path,"r", encoding="utf-8")
            json_file = json.load(json_file)
            info = file_extractor.extract_from_table(json_file)
            info = self.dict_to_readable_text(info)
            print("loaded file = ", file_path, info)
        if file_path.endswith(".json"):
            json_file = open(json_path,"r", encoding="utf-8")
            info = json.load(json_file)
            json_file.close()
            return info
    def dict_to_readable_text(self,data):
        if not isinstance(data, dict):
            return str(data)

        lines = []
        for title, info in data.items():
            lines.append(f"العنوان: {title}")

            if isinstance(info, dict):
                for k, v in info.items():
                    lines.append(f"- {k}: {v}")
            else:
                lines.append(f"- {info}")

            lines.append("")  # blank line between entries

        return "\n".join(lines)

    def run_the_ai(self,message_content):
        message_lang = detect_language(message_content)
        rules_f = None
        for lang, rules_file in self.rules_files.items():
            if lang == message_lang:
                rules_f = open(rules_file,"r", encoding="utf-8")
                break
        if rules_f == None:
            rules_f = open(self.rules_files["en"],"r", encoding="utf-8")
        rules = rules_f.read()
        rules_f.close()
        retrieved_chunks = self.find_relvant_info(message_content)

        if not retrieved_chunks:
            context = "No relevant information found."
        else:
            context = "\n\n".join([text for _, text in retrieved_chunks])
        system_prompt = context + "\n" + rules 
        print(system_prompt)

        self.temperature = 0.5 
        if len(system_prompt)>10000:
            self.num_predict = 5000
        elif len(system_prompt)>3000:
            self.num_predict = 3000
        else:
            self.num_predict = 2000
            
        answer = self.make_a_ai_respon(system_prompt, message_content)
        print(answer)
        return answer
