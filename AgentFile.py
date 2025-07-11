import zmq
import json
import os
import shutil

class AgentFile:
    def __init__(self, name="AgentFile", sub_port=5556, pub_port=5555):
        self.name = name
        self.ctx = zmq.Context()
        # SUB-сокет для получения задач
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(f"tcp://127.0.0.1:{sub_port}")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, f"agent.{self.name}.tasks")
        # PUB-сокет для отправки результатов
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.connect(f"tcp://127.0.0.1:{pub_port}")

    def handle(self, task: dict) -> dict:
        action = task["params"].get("action")
        path = task["params"].get("path")
        result = {}

        try:
            if action == "create_file":
                content = task["params"].get("content", "")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                result = {"status": "success", "msg": f"Файл {os.path.basename(path)} создан.", "path": path}

            elif action == "create_dir":
                os.makedirs(path, exist_ok=True)
                result = {"status": "success", "msg": f"Папка {path} создана.", "path": path}

            elif action == "read":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                result = {"status": "success", "content": content, "msg": f"Прочитан файл {os.path.basename(path)}."}

            elif action == "append":
                content = task["params"].get("content", "")
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
                result = {"status": "success", "msg": f"Данные добавлены в файл {os.path.basename(path)}."}

            elif action == "rename":
                new_path = task["params"].get("new_path")
                os.rename(path, new_path)
                result = {"status": "success", "msg": f"Файл/папка переименован.", "old_path": path, "new_path": new_path}

            elif action == "delete_file":
                os.remove(path)
                result = {"status": "success", "msg": f"Файл {os.path.basename(path)} удалён.", "path": path}

            elif action == "duplicate_file":
                new_path = task["params"].get("new_path")
                shutil.copy2(path, new_path)
                result = {"status": "success", "msg": f"Файл {os.path.basename(path)} дублирован.", "src": path, "dst": new_path}

            elif action == "copy_file":
                temp_dir = task["params"].get("temp_dir", "/tmp")
                temp_path = os.path.join(temp_dir, os.path.basename(path))
                shutil.copy2(path, temp_path)
                result = {"status": "success", "msg": f"Файл скопирован во временное хранилище.", "src": path, "dst": temp_path}

            elif action == "paste_file":
                src_path = task["params"].get("src_path")
                dst_path = task["params"].get("dst_path")
                shutil.copy2(src_path, dst_path)
                result = {"status": "success", "msg": f"Файл вставлен из {src_path} в {dst_path}."}

            else:
                result = {"status": "error", "msg": f"Неизвестное действие: {action}"}

        except Exception as e:
            result = {"status": "error", "msg": str(e)}

        return result

    def run(self):
        print(f"[{self.name}] Агент запущен, ожидание задач...")
        while True:
            topic, msg = self.sub.recv_multipart()
            task = json.loads(msg)
            print(f"[{self.name}] Получена задача: {task}")
            res = self.handle(task)
            envelope = {
                "task_id": task.get("task_id"),
                "agent": self.name,
                "result": res,
                "timestamp": task.get("timestamp")
            }
            self.pub.send_multipart([
                f"agent.{self.name}.results".encode(),
                json.dumps(envelope, ensure_ascii=False).encode("utf-8")
            ])
            print(f"[{self.name}] Отправлен результат: {envelope}")

if __name__ == "__main__":
    agent = AgentFile()
    agent.run()