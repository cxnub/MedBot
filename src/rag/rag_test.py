import requests

url = "https://594f-152-226-255-18.ngrok-free.app/query"
data = {"query": "What are the symptoms of flu?"}

response = requests.post(url, json=data)
print(response.json())
