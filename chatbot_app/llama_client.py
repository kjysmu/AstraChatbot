from langchain_ollama import OllamaLLM

class LlamaClient:
    def __init__(self, model="llama3"):
        self.model = model
        self.client = OllamaLLM(model=model)

    def invoke(self, prompt):
        response = self.client.invoke(prompt)
        return response