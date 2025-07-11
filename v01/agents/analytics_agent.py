from base_agent import BaseAgent
import numpy as np

class AnalyticsAgent(BaseAgent):
    def handle(self, task: dict) -> dict:
        data = task["params"].get("data", [])
        arr  = np.array(data)
        return {
            "mean": float(arr.mean()),
            "std":  float(arr.std())
        }
