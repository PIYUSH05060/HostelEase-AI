import json, urllib.request

def generate(system,prompt):
 payload={'model':'qwen2.5:3b','messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'stream':False,'options':{'num_predict':220,'temperature':0.2}}
 req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=90) as r: return json.load(r)['message']['content']
