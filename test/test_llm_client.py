from pathlib import Path
import sys
from typing import Annotated, TypedDict
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from utils.llm_client import LLMClient


class TestLLMClient:
    def test_client_structured_completion(self,):
        """Test LLM client connection and structured completion."""
        settings = get_settings()
        deepseek_model = LLMClient(settings.api_key, settings.api_base, settings.model_name)
        class TestSchema(TypedDict):
            """Test schema for structured output."""
            response: Annotated[str, "The response to the user"]
        response = deepseek_model.structured_completion(
            schema=TestSchema,
            messages=[
                # 某些模型要显示指定回答json否则报错, 有些不报错但是无法得到json格式
                # {"role": "system", "content": "You are a helpful assistant that responds in JSON format."},
                {"role": "user", "content": "你好"}
            ],
        )
        print(response)
        assert response["response"] is not None

