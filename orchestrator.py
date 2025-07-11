import zmq
import uuid
import time
import json
from llama_cpp import Llama

# ---- Загрузка модели llama.cpp через llama-cpp-python ----
# Укажи путь к своему .gguf файлу
MODEL_PATH = r"C:/Mi-01/v01/ggml-model-Q4_K_M.gguf"  # Например, "C:\\models\\llama-3-8b.gguf"
llm = Llama(
    model_path=MODEL_PATH, 
    n_ctx=2048,
    n_gpu_layers=35,
    n_batch=512,
    verbose=True
    )

PROMPT_TEMPLATE = """
Ты — координатор агентов. Преобразуй задачу пользователя в JSON для AgentFile.
Формат задачи:
[
  {{
    "agent": "AgentFile",
    "params": {{"action": ..., "path": ..., "content": ...}}
  }}
]
Примеры:
1. Создай файл C:\\tmp\\test.txt с текстом "Hello World!"
[
  {{
    "agent": "AgentFile",
    "params": {{"action": "create_file", "path": "C:\\\\tmp\\\\test.txt", "content": "Hello World!"}}
  }}
]
2. Создай папку D:\\new_folder
[
  {{
    "agent": "AgentFile",
    "params": {{"action": "create_dir", "path": "D:\\\\new_folder"}}
  }}
]
Верни только массив JSON-задач!
Задача пользователя: {user_task}
"""

def get_tasks_from_llm(user_task):
    prompt = PROMPT_TEMPLATE.format(user_task=user_task)
    output = llm(prompt, max_tokens=512, stop=["\n\n"])["choices"][0]["text"]
    # Найти массив JSON в выходе
    try:
        left = output.index("[")
        right = output.rindex("]") + 1
        tasks_json = output[left:right]
        tasks = json.loads(tasks_json)
    except Exception as e:
        print(f"Ошибка разбора JSON: {e}\nLLM output: {output}")
        tasks = []
    return tasks

# ----- ZeroMQ -----
ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5555")
sub = ctx.socket(zmq.SUB)
sub.bind("tcp://*:5556")
sub.setsockopt_string(zmq.SUBSCRIBE, "agent.AgentFile.results")

def publish_task(task):
    topic = f"agent.{task['agent']}.tasks"
    pub.send_multipart([topic.encode(), json.dumps(task, ensure_ascii=False).encode("utf-8")])

def listen_result(timeout=5000):
    if sub.poll(timeout):
        _, msg = sub.recv_multipart()
        return json.loads(msg)
    return None

if __name__ == "__main__":
    user_input = input("Опишите задачу для файлового агента: ")
    tasks = get_tasks_from_llm(user_input)

    for t in tasks:
        t["task_id"] = str(uuid.uuid4())
        t["timestamp"] = time.time()
        publish_task(t)
        print(f"Задача отправлена агенту: {t}")

    print("Ожидание результата...")
    start = time.time()
    while time.time() - start < 10:
        res = listen_result(timeout=1000)
        if res:
            print("✅ Результат:", res)
            break
    else:
        print("Время ожидания истекло.")
