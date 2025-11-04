# config.py
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
import yaml


def kebab_to_snake(name: str) -> str:
    """将 kebab-case 转为 snake_case"""
    if '_' in name:
        return name.replace("_", "-")
    else:
        return name


class KebabBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=kebab_to_snake,
        populate_by_name=True,  # 允许通过 Python 属性名（如 conversation_sidebar）访问，即使 YAML 中是 kebab-case
        str_strip_whitespace=True  # 自动去除字符串首尾空格（修正 base_url 末尾空格问题）
    )


class LoginConfig(KebabBaseModel):
    check_timeout: int = Field(10000, description="登录超时时间（毫秒）")
    op_timeout: int = Field(10000, description="登录操作超时时间（毫秒）")
    mode: str
    indicator_selector: str # 登录成功后页面中应存在的元素选择器，用于判断是否已登录



class ConversationConfig(KebabBaseModel):
    load_sidebar_timeout: int = Field(10000, description="加载对话列表超时时间（毫秒）")
    load_content_timeout: int = Field(10000, description="等待对话内容加载超时（毫秒）")
    sidebar_container: str # 包裹所有对话项的容器选择器
    group_container_selector: str | None = None # 分组列表容器选择器
    group_drag_selector: str | None = None # 分组下拉框选择器
    group_item_selector: str | None =  None
    group_status_selector: str | None = None
    group_open_status: str | None = None
    group_close_status: str | None = None
    item_selector: str # 单个对话项的选择器


class ExportConfig(KebabBaseModel):

    trigger_button_selector: str # 触发导出菜单的按钮选择器
    trigger_mode: str = Field("hover", description="触发菜单的触发方式")
    sub_menu_selector: str | None = None
    menu_item_selector: str # 菜单项的通用选择器
    main_export_keywords: List[str] = Field(
        ["下载", "导出", "Download", "Export"],
        description="用于识别主‘导出’菜单项的关键词列表"
    )
    json_export_keywords: List[str] = Field(
        ["JSON", "json", "导出为JSON", "Export as JSON"],
        description="用于识别‘导出为 JSON’子菜单项的关键词（若无子菜单可为空）"
    )
    timeout: int = Field(10000, description="等待导出选项出现超时时间（毫秒）")


class CrawlerConfig(KebabBaseModel):
    name: str # 应用名称
    base_url: str = Field("", description="网站基础 URL")
    login: LoginConfig = Field(default_factory=LoginConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    download_dir: Optional[str] = Field("", description="程序控制的下载目录（留空则使用浏览器默认）")


def load_config_from_yaml(path: str) -> CrawlerConfig:
    """从 YAML 文件加载配置并返回强类型 Pydantic 模型"""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return CrawlerConfig.model_validate(data)
