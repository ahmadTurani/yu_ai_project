import re

import ollama
import json
import numpy as np
import langid
import faiss

def detect_language(text):
    lang, confidence = langid.classify(text)
    return lang

class AiCreator:
    def __init__ (self, rules_files, ai_model, embedding_files, temperature,context_window=8024):
        self.rules_files = rules_files
        self.temperature = temperature
        self.ai_model = ai_model
        self.indices = self.make_a_index_for_alllangs(embedding_files)
        self.context_window = context_window
    
    def make_a_index_for_alllangs(self, embedding_files):
        indices = {}
        for lang, embedding_file in embedding_files.items():
            indices[lang] = self.make_fiass_index(embedding_file)
            
        return indices

    def make_fiass_index(self, embedding_file):
        # open the embedding file and load the embeddings
        with open(embedding_file,"r", encoding="utf-8") as f:
            embeddings = json.load(f)

        #create a matrix of the embeddings 
        embeddings_list = [item["embedding"] for item in embeddings]

        # convert the list of embeddings to a numpy array and ensure it's 2D
        vector_matrix = np.array(embeddings_list).astype('float32')
        vector_matrix = np.squeeze(vector_matrix, axis= 1)

        # normalize the vectors in the matrix
        faiss.normalize_L2(vector_matrix)

        # create a FAISS index and add the vectors to it
        dimensions = vector_matrix.shape[1]
        index = faiss.IndexFlatIP(dimensions)
        index.add(vector_matrix)
        return index, embeddings
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

    def find_relvant_info(self, message_content, number_of_retrievaled_info=2, lang=None):
        # 1. Embed the user's message using Ollama
        response = ollama.embed(model="qwen3-embedding", input=message_content)
        query_vec = np.array(response.embeddings).astype('float32').reshape(1, -1)
        
        # 2. Normalize the query
        faiss.normalize_L2(query_vec)

        # 3. Search the FAISS Index
        # D is a list of scores, I is a list of row indices
        if not lang or lang not in self.indices:
            lang = next(iter(self.indices))
        index = self.indices[lang][0]  # Get the FAISS index for the specified language
        scores, row_indices = index.search(query_vec, number_of_retrievaled_info)

        # 4. Format the output to match your old "unique_similarities" style
        results = []
        for i in range(len(row_indices[0])):
            idx = row_indices[0][i]
            if idx != -1:
                score = float(scores[0][i])
                chunk = self.indices[lang][1][idx]
                
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
                'num_ctx': self.context_window
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

    def run_the_ai(self, message_content, speed="fast"):
        message_lang = detect_language(message_content) or "ar" # Default to Arabic
    
        # تحسين قراءة ملف القوانين
        rules_path = self.rules_files.get(message_lang, self.rules_files["en"])
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = f.read()

        retrieved_chunks = self.find_relvant_info(message_content, lang=message_lang)

        if not retrieved_chunks:
            context = "عذراً، لا توجد معلومات كافية في قاعدة البيانات للإجابة على هذا السؤال."
        else:
            formatted_chunks = []
            for i, chunk in enumerate(retrieved_chunks, 1):
                urls = chunk.get("relevant_urls", {})

                # Fix: Clean URLs before formatting
                cleaned_urls = {}
                for k, v in urls.items():
                    # Extract only the actual URL part (stop at any non-URL character)
                    url_match = re.match(r'(https?://[^\s•]+)', str(v))
                    cleaned_urls[k] = url_match.group(1) if url_match else v

                urls_formatted = "\n".join([f"  * {k}: {v}" for k, v in cleaned_urls.items()]) if cleaned_urls else "لا توجد روابط."
            
                block = (
                    f"### المرجع [{i}]: {chunk['title']}\n"
                    f"- المصدر: {chunk['source']}\n"
                    f"- النص الحرفي: {chunk['text']}\n"
                    f"- الروابط المتاحة:\n{urls_formatted}\n"
                    f"{'-' * 30}"
                )
                formatted_chunks.append(block)
        
            context = "\n\n".join(formatted_chunks)

        # بناء البرومبت النهائي (الاستراتيجية المطورة)
        final_system_prompt = (
            f"{rules}\n\n"
            f"{context}\n\n"
            f"تنبيه هام للمساعد: التزم بالقوانين السابقة حرفياً، خاصة القاعدة رقم 9 و10."
        )
        print("---- System Prompt Preview ----")
        print(final_system_prompt)
        print("--- System Prompt Sent ---") # للتصحيح فقط
        answer = self.make_a_ai_respon(final_system_prompt, message_content, speed)
        return answer
