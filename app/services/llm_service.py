import json
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_PATH)
        self.model = AutoModelForCausalLM.from_pretrained(settings.LLM_MODEL_PATH)
        self.generator = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)
        self.embedder = pipeline("feature-extraction", model=self.model, tokenizer=self.tokenizer)

    async def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """
        Generate text based on the given prompt.
        """
        result = self.generator(prompt, max_length=max_length, num_return_sequences=1)
        return result[0]['generated_text']

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON response based on the given prompt.
        """
        result = await self.generate_text(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # If the generated text is not valid JSON, attempt to extract JSON-like content
            start = result.find('{')
            end = result.rfind('}')
            if start != -1 and end != -1:
                json_str = result[start:end+1]
                return json.loads(json_str)
            else:
                raise ValueError("Generated text does not contain valid JSON")

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get the embedding vector for the given text.
        """
        result = self.embedder(text)
        # The result is typically a list of lists, where each inner list represents a token.
        # We'll take the mean of all token embeddings to get a single vector for the entire text.
        return list(map(float, result[0].mean(axis=0)))

    async def evaluate_ethics(self, scenario: str, guidelines: List[str]) -> Dict[str, Any]:
        """
        Evaluate the ethical implications of a given scenario based on provided guidelines.
        """
        prompt = f"""
        Given the following scenario:
        {scenario}

        And considering these ethical guidelines:
        {' '.join(guidelines)}

        Provide an ethical evaluation including:
        1. An overall ethical score (0-100)
        2. Explanation of the ethical implications
        3. Potential concerns
        4. Suggestions for improvement

        Format your response as a JSON object.
        """
        return await self.generate_json(prompt)

    async def summarize(self, text: str, max_length: int = 100) -> str:
        """
        Generate a summary of the given text.
        """
        prompt = f"Summarize the following text in no more than {max_length} words:\n\n{text}\n\nSummary:"
        return await self.generate_text(prompt, max_length=max_length)

    async def answer_question(self, context: str, question: str) -> str:
        """
        Answer a question based on the given context.
        """
        prompt = f"""
        Context: {context}

        Question: {question}

        Answer:
        """
        return await self.generate_text(prompt)

    async def generate_ethics_scenario(self, topic: str) -> Dict[str, Any]:
        """
        Generate an ethics scenario based on a given topic.
        """
        prompt = f"""
        Generate an AI ethics scenario related to the topic: {topic}

        Include the following in your response as a JSON object:
        1. A brief description of the scenario
        2. Three possible actions that could be taken
        3. The ethical implications of each action

        Format your response as a JSON object.
        """
        return await self.generate_json(prompt)

    async def evaluate_knowledge_entry(self, entry: str) -> Dict[str, float]:
        """
        Evaluate the quality and relevance of a knowledge entry.
        """
        prompt = f"""
        Evaluate the following knowledge entry:
        {entry}

        Provide scores for:
        1. Quality (0-100): How well-written, accurate, and valuable is the content?
        2. Relevance (0-100): How relevant is this entry to AI ethics and responsible AI development?

        Format your response as a JSON object with "quality" and "relevance" keys.
        """
        result = await self.generate_json(prompt)
        return {
            "quality": float(result.get("quality", 0)),
            "relevance": float(result.get("relevance", 0))
        }

    async def translate(self, text: str, target_language: str) -> str:
        """
        Translate the given text to the target language.
        """
        prompt = f"Translate the following text to {target_language}:\n\n{text}\n\nTranslation:"
        return await self.generate_text(prompt)