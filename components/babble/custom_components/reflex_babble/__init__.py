from .babble import *
from .state import MODEL_REGISTRY
from .openai import openai_process_question
from .ollama import ollama_process_question

MODEL_REGISTRY['openai'] = openai_process_question
MODEL_REGISTRY['ollama'] = ollama_process_question