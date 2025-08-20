import ollama
from typing import Dict, Any, Optional, Type, Union, List
from pydantic import BaseModel

class OllamaGenerator:
    """
    A reusable Ollama client
    """
    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None):
        self.default_model = default_model
        self.default_options = {"temperature": 0.1}
        ollama.api_base = base_url

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        response_format: Optional[Union[Type[BaseModel], Dict]] = None,
        images: Optional[List[bytes]] = None,
    ) -> Dict[str, Any]:
        """
        Generate using Ollama.

        Args:
            prompt: The input prompt
            system: System message/instructions
            model: Model to use (overrides default)
            options: Generation options (temperature, top_p, etc.)
            response_format: Pydantic model or dict schema for structured output

        Return:
            Generated response as dictionary

        Raises:
            Exception: If generation fails
        """
        used_model = model or self.default_model
        used_options = {**self.default_options, **(options or {})}

        format_schema = None
        if response_format:
            if hasattr(response_format, 'model_json_schema'):
                format_schema = response_format.model_json_schema()
            elif isinstance(response_format, dict):
                format_schema = response_format

        try:
            generate_args = {
                "model": used_model,
                "prompt": prompt,
                "system": system,
                "options": used_options,
                "format": format_schema,
            }
            if images is not None:
                generate_args["images"] = images

            response = ollama.generate(**generate_args)
            return response

        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")
