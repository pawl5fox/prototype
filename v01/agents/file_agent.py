from base_agent import BaseAgent
import os

class FileAgent(BaseAgent):
    def handle(self, task: dict) -> dict:
        action = task["params"].get("action")
        path   = task["params"].get("path")
        if action == "list":
            files = os.listdir(path or ".")
            return {"files": files}
        elif action == "mkdir":
            os.makedirs(path, exist_ok=True)
            return {"status": "created", "path": path}
        else:
            return {"error": f"Unknown action '{action}'"}
