import queue,threading,pyttsx3
from config import VOICE_RATE,VOICE_VOLUME
class NovaTTS:
    def __init__(self,status_callback=None):
        self.status=status_callback or (lambda x:None); self.q=queue.Queue(); self.stop_event=threading.Event(); threading.Thread(target=self._worker,daemon=True).start()
    def speak(self,text):
        if text: self.q.put(str(text))
    def stop(self):
        while True:
            try: self.q.get_nowait(); self.q.task_done()
            except queue.Empty: break
    def _worker(self):
        while not self.stop_event.is_set():
            try: text=self.q.get(timeout=.2)
            except queue.Empty: continue
            try:
                self.status('SPEAKING'); e=pyttsx3.init(); e.setProperty('rate',VOICE_RATE); e.setProperty('volume',VOICE_VOLUME); e.say(text); e.runAndWait(); e.stop()
            except Exception as ex: self.status('TTS ERROR: '+str(ex))
            finally: self.q.task_done()
