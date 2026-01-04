from ..exceptions import UnsupportedPlatformError
from ..parsers.qwen_parser import QwenParser
# 如果有其他parser，在这里导入
# from ..parsers.chatgpt_parser import ChatGPTParser

class ParserFactory:
    # 平台名称到解析器类的映射表
    _parsers = {
        "qwen": QwenParser,
        # "chatgpt": ChatGPTParser,
    }

    @classmethod
    def get_parser(cls, platform_name: str):
        """
        根据平台名称获取解析器实例

        Args:
            platform_name: 平台标识符 (如 "qwen", "chatgpt")

        Returns:
            BaseParser 实例

        Raises:
            UnsupportedPlatformError: 当平台不支持时
        """
        platform_name = platform_name.lower()
        parser_class = cls._parsers.get(platform_name)
        
        if not parser_class:
            raise UnsupportedPlatformError(f"Platform '{platform_name}' is not currently supported.")
            
        return parser_class()