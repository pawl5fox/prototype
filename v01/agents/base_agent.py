import zmq
import uuid
import json
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name: str, zmq_context: zmq.Context, sub_port: int, pub_port: int):
        self.name = name
        self.ctx = zmq_context
        # SUB-сокет для получения задач
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(f"tcp://127.0.0.1:{sub_port}")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, f"agent.{name}.tasks")
        # PUB-сокет для отправки результатов
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.connect(f"tcp://127.0.0.1:{pub_port}")

    @abstractmethod
    def handle(self, task: dict) -> dict:
        """
        Основная логика агента:
        принимает task, возвращает result-словарь.
        """
        pass

    def run(self):
        while True:
            topic, msg = self.sub.recv_multipart()
            payload = json.loads(msg)
            result = self.handle(payload)
            envelope = {
                "task_id": payload["task_id"],
                "agent": self.name,
                "result": result,
                "timestamp": payload.get("timestamp")
            }
            self.pub.send_multipart([
                f"agent.{self.name}.results".encode(),
                json.dumps(envelope).encode()
            ])
