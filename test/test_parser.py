import pytest
from pathlib import Path
import sys
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from agents.workflow.parser.core.factory import ParserFactory


class TestParser:
    """Test parser functionality."""
    def test_qwen_parser_single(self,):
        """Test Qwen parser with single round conversation."""
        factory = ParserFactory()
        parser = factory.get_parser("qwen")
        assert parser is not None
        file_path = project_root / "conversations" / "qwen_test.json"
        with open(file_path, "r", encoding="utf-8") as f:
            import json
            raw_data = json.load(f)
        result = parser.parse(raw_data)
        print(f"共解析{len(result)}条记录")
    
    def test_qwen_parser_total(self,):
        """Test Qwen parser with total conversation."""
        factory = ParserFactory()
        parser = factory.get_parser("qwen")
        assert parser is not None
        file_path = project_root / "conversations" / "qwen_total_test.json"
        with open(file_path, "r", encoding="utf-8") as f:
            import json
            raw_data = json.load(f)
        result = parser.parse(raw_data)
        print(f"共解析{len(result)}条记录")

