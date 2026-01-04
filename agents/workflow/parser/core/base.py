from abc import ABC, abstractmethod
from typing import Any

class BaseParser(ABC):
    """
    解析器抽象基类
    所有平台的解析器必须继承此类并实现 parse 方法
    """

    @abstractmethod
    def parse(self, raw_data: Any) -> list[list[dict[str, str]]]:
        """
        解析原始 JSON 数据，转换为标准格式

        Args:
            raw_data: 原始 JSON 数据 (dict 或 list)

        Returns:
            list[list[dict[str, str]]]: 标准二维数组结构
            [
                [
                    {"title": "标题1", "question": "问题1", "answer": "回答1"},
                    ...
                ],
                ...
            ]
        """
        pass

    def _format_conversation(self, title: str, question: str, answer: str) -> dict[str, str]:
        """辅助方法：格式化单条对话记录"""
        return {
            "title": title,
            "question": question,
            "answer": answer
        }