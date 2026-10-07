import json
from http.server import BaseHTTPRequestHandler, HTTPServer 

import requests
import re

from tools import *

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"

def is_long(answer):
    return "````" in answer or len(answer) > 300 or answer.count("\n") > 3

def split_intro(text):
    m = re.search(r"```|\n\s*\n", text)
    if not m:
        return text, ""
    return text[:m.start()].strip(), text[m.start():].strip()

characterPrompt: str = """
You are JARVIS, the AI butler from Iron Man, speaking out loud to the user through their Linux laptop.

How you speak:
- Calm, precise, and unfailingly polite, with a dry, understated British wit.
- Address the user as "sir".
- One or two short sentences. Your words are read aloud, so no lists, markdown, or emoji.
- If the plain result contains technical information (code, numbers), do not overwrite it no matter what. You may pad around it.

Rules:
- You are given the user's request and the plain result of what was done. Your only goal is to reword that result in your voice while maintaining all of the information.
- Keep every fact exactly as given: times, numbers, names. Never add facts, estimates, or offers to do things that are not in the result.

Examples:
Request: what time is it
Result: It's 06:02 PM.
JARVIS: It's 6:02 in the evening, sir.

Request: open the terminal
Result: Opening terminal.
JARVIS: Terminal's up, sir. Do try not to break anything.

Request: open spotify
Result: No installed app matches 'spotify'.
JARVIS: I'm afraid Spotify isn't installed, sir.
"""

def ask_char(request, result):
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "stream": False,
        "think": False,
        "messages": [
                {"role": "system", "content": characterPrompt},
                {"role": "user",   "content": f"Request: {request}\nResult: {result}"}
            ],
        "options": {"temperature": 0.7, "num_ctx": 16384},
        })
    return resp.json()["message"]["content"] + (result if is_long(result) else "")


def personaify(request, result):
    out = ""
    if not is_long(result):
        return ask_char(request, result)

    lead, rest = split_intro(result)

    if not lead or len(lead) > 300:
        intro = ask_char(request, "The full answer is shown on the screen below what you say. Introduce it in one sentence without repeating its contents.")
        return intro + "\n" + result
    return ask_char(request, lead) + "\n" + rest

def ask_qwen(prompt):
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "stream": False,
        "think": False,
        "messages": prompt,
        "tools": TOOLS,
        "options": {"temperature": 0.1, "num_ctx": 16384},
        })
    #print(resp.json()["message"]["content"])
    return resp.json()["message"]

def handle(text: str):
    prompt = [
            {"role": "system", "content": """You are an assistant with access to a Linux computer, you can run a select few tools. Your purpose is to be useful.
             If you get blocked from using a tool, report that information directly to the user, along with the exact tool name and arguments you tried running. Do not keep trying to reuse it.""" },
            {"role": "user", "content": text}
            ]
    for _ in range(25):
        message = ask_qwen(prompt)
        prompt.append(message)
        if not message.get("tool_calls"):
            return personaify(text, message["content"])
        for call in message.get("tool_calls"):
            name = call["function"]["name"]
            func = FUNCTIONS.get(name)
            print(f"Trying to run {name}")
            result = func(**call["function"]["arguments"]) if func else f"Unknown tool {name}"
            prompt.append({"role": "tool", "tool_name": name, "content": result})
    return "timed out from too many calls, " + personaify(text, message["content"])



class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        text = json.loads(self.rfile.read(length))["text"]
        print("Got:", text)
        body = json.dumps({"reply": handle(text)}).encode()
        #print("Handled text: ", handle(text))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

print("Agent listening on http://127.0.0.1:8801")
HTTPServer(("127.0.0.1", 8801), Handler).serve_forever()
