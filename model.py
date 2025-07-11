from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

tokenizer = AutoTokenizer.from_pretrained("ruslandev/llama-3-8b-gpt-4o-ru1.0")
model = AutoModelForCausalLM.from_pretrained("ruslandev/llama-3-8b-gpt-4o-ru1.0")
