from base_agent import BaseAgent
import requests

class APIAgent(BaseAgent):
    def handle(self, task: dict) -> dict:
        url    = task["params"].get("url")
        method = task["params"].get("method", "GET").upper()
        try:
            resp = requests.request(method, url, params=task["params"].get("params"))
            return {"status_code": resp.status_code, "body": resp.json()}
        except Exception as e:
            return {"error": str(e)}
