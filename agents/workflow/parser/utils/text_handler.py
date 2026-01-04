import json

def decode_unicode_escapes(text):
    """
    解析 JSON 中的 Unicode 转义字符 (例如 \u4e0b)
    """
    if not isinstance(text, str):
        return text
    try:
        # 将字符串编码为 bytes，再以 unicode-escape 解码回来
        return text.encode("utf-8").decode("unicode-escape")
    except (UnicodeDecodeError, AttributeError):
        return text

def clean_title(title):
    """清洗标题，去除默认标题中的无效字符"""
    if not title:
        return ""
    # 这里可以添加更多清洗逻辑
    return title.strip()