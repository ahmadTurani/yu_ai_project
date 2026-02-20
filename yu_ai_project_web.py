#remove all comments tags when ready to run on scale after instaling everything needed 
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import agent_creator as yp  
#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address
from queue import Queue, Empty
#from redis import Redis

agent_pool = Queue()
with open("ai_agent_creator.json", "r", encoding="utf-8") as f:
    ai_agents_data = json.load(f)

ai_list = []
for agent_name, agent_config in ai_agents_data.items():
    if agent_config["activation"] :
        ai_list.append(agent_name)
        for i in range(agent_config["number_of_copies"]):
            agent_copy = yp.AiCreator(
                agent_config["key_words_to_files"],
                agent_config["keys_rules_file"],
                agent_config["rules_files"],
                agent_config["ai_model"],
                agent_config["embedding_file"],
                agent_config["temperature"]
            )
            agent_pool.put(agent_copy)
    else:
        pass
    
#web working logic
def process_request(message):
    try:
        agent = agent_pool.get(timeout=20)
    except Empty:
        return "الخادم مشغول حالياً، حاول لاحقاً"  
    try:
        response = agent.run_the_ai(message)
        return response
    finally:
        agent_pool.put(agent)
if not ai_list:
    raise Exception("No active AI agents")
app = Flask(__name__)    
#r = Redis(host='localhost', port=6379, db=0)
#limiter = Limiter(
#    app=app,
#    key_func=get_remote_address,
#    storage_uri="redis://localhost:6379",
#    default_limits=["30 per hour"]
#)

CORS(app, resources={
    r"/ask": {"origins": ["https://yourdomain.com"]}
})
@app.route('/')
def serve_index():
    return send_file('yu_ai.html')

@app.route('/ask', methods=['POST'])
#@limiter.limit("4 per minute")
def ask():
    try:
        print("active agents models : ", ai_list)
        data = request.get_json(force=True)
        message = data.get('message', '')
        if not isinstance(message, str) or not message.strip():
            return jsonify({'success': False, 'response': 'يرجى إدخال سؤال.'})

        if len(message) > 1500:
            return jsonify({'success': False, 'response': 'الرسالة طويلة جداً'})
        response = process_request(message)
        
        return jsonify({'success': True, 'response': response})
    
    except Exception as e:
        print("ERROR:", e)
        return jsonify({'success': False, 'response': 'حدث خطأ داخلي'})
if __name__ == '__main__':
    print("Starting Yarmouk University AI Assistant server...")
    app.run(port=5000, host='0.0.0.0')