import requests
import json

KEY_OLLAMA     = "ollama"
URL_OLLAMA     = "http://localhost:11434/v1/chat/completions"
MDL_OLLAMA     = "qwen2.5:7b"
with open("config_llm.txt", "r") as f:
    config_llm = f.readlines()
    URL_OLLAMA = config_llm[0].strip()
    MDL_OLLAMA = config_llm[1].strip()
print(URL_OLLAMA)
print(MDL_OLLAMA)

class RequestInput:
    def __init__(self, prompt, stream=False, vendor="ollama"):

        if vendor=="ollama":
            LLM_API_KEY = KEY_OLLAMA
            LLM_API_URL = URL_OLLAMA
            LLM_API_MDL = MDL_OLLAMA

        self.url = LLM_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        self.payload = {
            "stream": stream,
            "model": LLM_API_MDL,
            "messages": [ { "role": "user", "content": prompt } ]
        }
        self.stream = stream

# Non-streaming
def Process_LLM(prompt):
    reqin = RequestInput(prompt=prompt, stream=False)
    try:
        with requests.post(url=reqin.url, headers=reqin.headers, json=reqin.payload, stream=reqin.stream) as req:
            return req.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️ LLM > {e}")
        return "⚠️"

# Streaming
def Process_LLM_Stream(prompt, history=[]):
    history += [{"role":"assistant", "content":""}]
    reqin = RequestInput(prompt=prompt, stream=True)
    try:
        with requests.post(url=reqin.url, headers=reqin.headers, json=reqin.payload, stream=reqin.stream) as req:
            for chunk in req.iter_lines():
                if chunk:
                    chunk = chunk.decode("utf-8", errors="replace")[6:]
                    try:
                        chunk = json.loads(chunk)["choices"][0]["delta"]["content"]
                        history[-1]["content"] += chunk
                        yield history
                    except:
                        pass
    except Exception as e:
        print(f"⚠️ LLM > {e}")
        history[-1]["content"] += "⚠️"
        yield history

try:
    Process_LLM("xin chào")
except:
    raise ValueError(f"⚠️ Cannot connect LLM server: {URL_OLLAMA} ({MDL_OLLAMA})")