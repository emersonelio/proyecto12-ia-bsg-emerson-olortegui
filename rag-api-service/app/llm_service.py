import os
from openai import OpenAI


class LLMService:

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "400"))
        self.temperature = float(os.getenv("TEMPERATURE", "0"))

        if not self.api_key:
            raise ValueError("Falta OPENAI_API_KEY en el archivo .env")

        self.client = OpenAI(api_key=self.api_key)

    def generate_answer(self, question: str, context: str) -> str:
        prompt = f"""
Eres un asistente experto en documentación de procesos RPA.

Reglas:
1. Responde únicamente usando el contexto proporcionado.
2. No inventes información.
3. Si el contexto no contiene la respuesta, indica:
"No encontré información suficiente en los documentos indexados."
4. Responde en español claro y profesional.
5. Si existen excepciones, acciones, responsables o sistemas mencionados, inclúyelos.

Contexto:
{context}

Pregunta:
{question}
"""

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=self.max_tokens,
            temperature=self.temperature
        )

        return response.output_text