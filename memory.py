import json
from pathlib import Path
from datetime import datetime
MEMORY_FILE=Path(__file__).with_name('nova_memory.json')
def load_memory():
    if not MEMORY_FILE.exists(): return {'facts':[]}
    try: return json.loads(MEMORY_FILE.read_text(encoding='utf-8'))
    except Exception: return {'facts':[]}
def save_memory(data): MEMORY_FILE.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def remember(text):
    data=load_memory(); data.setdefault('facts',[]).append({'text':text,'saved_at':datetime.now().isoformat(timespec='seconds')}); data['facts']=data['facts'][-100:]; save_memory(data); return 'I saved that to NOVA memory.'
def get_memory_context():
    facts=load_memory().get('facts',[])[-20:]
    return '\n'.join('- '+x['text'] for x in facts) if facts else 'No saved memory.'
