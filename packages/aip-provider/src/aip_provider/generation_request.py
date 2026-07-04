from aip_provider.generation_options import GenerationOptions
from pydantic import BaseModel


class GenerationRequest(BaseModel):

    prompt: str

    system_prompt: str | None = None

    options: GenerationOptions | None = None
