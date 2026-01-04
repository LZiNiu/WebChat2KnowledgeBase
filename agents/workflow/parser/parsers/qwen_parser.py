# 为了能导入父级目录的模块，通常在包结构中直接import即可
# 这里为了演示导入路径，假设是在包内运行
from ..core.base import BaseParser
from ..utils.text_handler import clean_title

class QwenParser(BaseParser):
    def parse(self, raw_data) -> list[list[dict[str, str]]]:
        """
        解析 Qwen 导出数据
        期望输入格式:
        >>> {"success": True, "data": [...]}
        或者单个对话窗口
        >>> [{...}]
        输出格式:
        >>> [[{"title": "对话窗口标题", "question": "用户问题", "answer": "助手回答"}]]
        """
        standard_result = []

        # 1. 获取对话窗口列表
        # 例如：conversations = raw_data.get("data", [])
        # 情况1: 直接包含所有对话窗口
        if isinstance(raw_data, dict):
            conversations: list[dict] | None = raw_data.get("data", None)
            if conversations is None:
                raise ValueError("Invalid Qwen data format: missing 'data' key")
        # 情况2: 仅包含单个对话窗口
        elif isinstance(raw_data, list):
            conversations = raw_data
        else:
            raise ValueError("Invalid Qwen data format: expected dict or list")
        for conv in conversations:
            # 初始化当前对话窗口的结果列表
            current_conv_records = []
            
            # 2. 获取当前对话的标题
            # 例如：title = conv.get("title", "")
            # if "默认标题" in title: title = ""
            title: str = conv["title"]
            if title is None or title.find("新聊天")!=-1:
                title = ""

            # 3. 获取当前对话的消息列表
            # 例如：messages = conv.get("content_list", [])
            messages: list[dict] = conv["chat"]["messages"]
            question: str | None = None
            answer: str | None = None
            for msg in messages:
                # 4. 提取 Question 和 Answer
                # 根据 msg 中的 role (user/assistant) 来区分
                # 这里假设问答是配对的
                if msg["role"] == "user":
                    question = msg["content"]
                    continue
                # 考虑回复出错的情况
                if msg["error"] is not None:
                    # 跳过当前问答对
                    question = None
                    continue
                answer = msg.get("content", "")
                if answer is None or len(answer) == 0:
                    # 有可能不在content_list字段, 尝试直接从content字段获取
                    # 从content_list中提取第一个content
                    answer = msg.get("content_list", [{}])[0].get("content", None)
                
                if question and answer:
                    # 将单条记录加入当前对话窗口
                    record = self._format_conversation(title, question, answer)
                    current_conv_records.append(record)
                    question, answer = None, None
            
            if current_conv_records:
                standard_result.append(current_conv_records)

        return standard_result