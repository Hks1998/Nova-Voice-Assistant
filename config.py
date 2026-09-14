import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY=os.getenv('GROQ_API_KEY','').strip()
COMPOUND_MODEL=os.getenv('NOVA_COMPOUND_MODEL','groq/compound')
LOCAL_AGENT_MODEL=os.getenv('NOVA_LOCAL_MODEL','openai/gpt-oss-120b')
VOICE_RATE=int(os.getenv('NOVA_VOICE_RATE','175'))
VOICE_VOLUME=float(os.getenv('NOVA_VOICE_VOLUME','1.0'))
MAX_HISTORY=int(os.getenv('NOVA_MAX_HISTORY','12'))
SYSTEM_PROMPT='''You are NOVA, a capable desktop AI assistant. Be concise but useful. Use available desktop tools when appropriate. Never claim an action succeeded unless the tool reports success. Ask for confirmation before potentially destructive actions.'''
