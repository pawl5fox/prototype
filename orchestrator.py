# orchestrator.py
import os
import json
import uuid
import time
import zmq
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ——— Настройка модели —————————————————————————————
MODEL_PATH = "C:/Mi-01/v01/ggml-model-Q4_K_M.gguf"  # например, "./model"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    device_map="auto"
)
model.to(DEVICE)

# ——— Функция генерации задач ——————————————————————
def generate_tasks(user_input: str) -> str:
    prompt = (
        f"Ты — координатор агентов. Задача: {user_input}\n"
        "Разбей её на подзадачи в формате JSON:\n"
        "[{\"agent\": \"file\", \"params\": {\"action\": \"`, ...}}]\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.2,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ——— ZeroMQ —————————————————————————————————————————
ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5555")
sub = ctx.socket(zmq.SUB)
sub.bind("tcp://*:5556")
sub.setsockopt_string(zmq.SUBSCRIBE, "agent.")

def publish_task(task: dict):
    topic = f"agent.{task['agent']}.tasks"
    pub.send_multipart([topic.encode(), json.dumps(task).encode()])

def listen_results(timeout=5000):
    if sub.poll(timeout):
        _, msg = sub.recv_multipart()
        return json.loads(msg)
    return None

# ——— Главная логика ——————————————————————————————
if __name__ == "__main__":
    user_input = input("Введите задачу: ")
    raw = generate_tasks(user_input)
    try:
        tasks = json.loads(raw)
    except json.JSONDecodeError:
        print("Ошибка разбора JSON:", raw)
        exit(1)

    for t in tasks:
        t.setdefault("agent", t.get("agent", "file"))
        t.setdefault("params", {})
        t["task_id"] = str(uuid.uuid4())
        t["timestamp"] = time.time()
        publish_task(t)
        print(f"> Опубликовал задачу {t['task_id']} → {t['agent']}")

    print("Ожидаем результаты...")
    start = time.time()
    while time.time() - start < 10:
        res = listen_results(timeout=1000)
        if res:
            print("✅ Результат:", res)
