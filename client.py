import requests


while True:
    text = input("> ")
    resp = requests.post("http://127.0.0.1:8801", json={"text": text})
    print(resp.json()["reply"])

