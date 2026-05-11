import ollama
import json
import numpy as np
import langid
import faiss

def detect_language(text):
    lang, confidence = langid.classify(text)
    return lang

class AiCreator:
    def __init__ (self, rules_files, ai_model, embedding_file, temperature):
        self.rules_files = rules_files
        self.temperature = temperature
        self.ai_model = ai_model
        f = open(embedding_file,"r", encoding="utf-8")
        self.embeddings = json.load(f)
        f.close
        embeddings_list = [item["embedding"] for item in self.embeddings]
        self.vector_matrix = np.array(embeddings_list).astype('float32')
        self.vector_matrix = np.squeeze(self.vector_matrix, axis= 1)
        faiss.normalize_L2(self.vector_matrix)
        dimensions = self.vector_matrix.shape[1]
        self.index = faiss.IndexFlatIP(dimensions)
        self.index.add(self.vector_matrix)        
    def embed_messages(self,message_content):
        response = ollama.embed(
            model="qwen3-embedding",
            input=message_content
            )
        query_vec = np.array(response.embeddings).astype('float32')
        if len(query_vec.shape) == 1:
            query_vec = query_vec.reshape(1, -1)
        faiss.normalize_L2(query_vec)
        return query_vec

    def find_relvant_info(self, message_content, number_of_retrievaled_info=2):
        # 1. Embed the user's message using Ollama
        response = ollama.embed(model="qwen3-embedding", input=message_content)
        query_vec = np.array(response.embeddings).astype('float32').reshape(1, -1)
        
        # 2. Normalize the query
        faiss.normalize_L2(query_vec)

        # 3. Search the FAISS Index
        # D is a list of scores, I is a list of row indices
        scores, row_indices = self.index.search(query_vec, number_of_retrievaled_info)

        # 4. Format the output to match your old "unique_similarities" style
        results = []
        for i in range(len(row_indices[0])):
            idx = row_indices[0][i]
            if idx != -1:
                score = float(scores[0][i])
                chunk = self.embeddings[idx]
                
                results.append({
                    "score": score,
                    "text": chunk["text"],
                    "title": chunk["title"],
                    "source": chunk["source"],
                    "relevant_urls": chunk["relevant_urls"]
                })
        return results
    def make_a_ai_respon(self,system_prompt,message_content, speed):
        response = ollama.chat(model=self.ai_model[speed], messages=[
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
                })
        
        return response['message']['content']
    def build_keys_prompt(self):
        lines = ["المفاتيح المتاحة:"]
        for key in self.keywords.keys():
            lines.append(f"- {key}")
        return "\n".join(lines)
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

    def run_the_ai(self,message_content,speed="fast"):
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
            context = "\n\n".join(
                f"""title: {chunk['title']}
                sorce: {chunk['source']}
                content: {chunk['text']}
                relevant urls: {chunk["relevant_urls"]} """
            for chunk in retrieved_chunks )

        system_prompt = context + "\n" + rules 
        print(system_prompt)
            
        answer = self.make_a_ai_respon(system_prompt, message_content, speed)
        print(answer)
        return answer
