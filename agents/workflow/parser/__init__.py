from typing import Any
from .core.factory import ParserFactory
from .exceptions import UnsupportedPlatformError
from utils.logger import get_tool_logger

logger = get_tool_logger()
def parse_chat_data(raw_data: Any, platform_name: str) -> list[list[dict[str, str]]]:
    """
    工作流节点入口函数
    
    Args:
        raw_data: 导出的原始 JSON 数据 (dict 或 list)
        platform_name: 平台名称 (例如 "qwen")

    Returns:
        标准化后的二维对话数组
        
    Example:
        >>> data = {"success": True, "data": [...]}
        >>> result = parse_chat_data(data, "qwen")
    """
    logger.info("=== Begin parse chat data ===")
    try:
        # 1. 获取解析器
        parser = ParserFactory.get_parser(platform_name)
        
        # 2. 执行解析
        parsed_result = parser.parse(raw_data)
        logger.info("parse total %d conversations", sum(len(conv) for conv in parsed_result))
        logger.info("=== End parse chat data ===")
        return parsed_result
        
    except UnsupportedPlatformError as e:
        # 在实际工作流中，可以记录日志或返回特定的错误结构
        logger.error(f"Error: {e}")
        raise e
    except Exception as e:
        # 捕获其他未知异常（如JSON结构错误导致的KeyError）
        logger.error(f"An unexpected error occurred during parsing: {e}")
        raise e