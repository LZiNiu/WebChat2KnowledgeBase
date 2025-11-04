import json
import asyncio
from typing import Dict, List
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, Download, Playwright, TimeoutError, BrowserContext, Browser, \
    ElementHandle

from CrawlBrowser.config.crawler_config import load_config_from_yaml

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s-%(threadName)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

class ExportCrawler(ABC):
    def __init__(self, platform_config_path: str | Path):
        if isinstance(platform_config_path, Path):
            platform_config_path = str(platform_config_path)
        logging.info(f"初始化配置文件: {Path(platform_config_path).absolute()}")
        self.config = load_config_from_yaml(platform_config_path)
        logging.info(f"已加载配置!")

        base_dir = Path(__file__).parent.parent
        self.platform_name = self.config.name
        self.login_config = self.config.login
        # 登录状态存储目录
        self.auth_state_path = base_dir / "auth_states" / f"{Path(platform_config_path).stem}_auth_state.json"
        # 下载目录
        if self.config.download_dir:
            self.download_dir = Path(self.config.download_dir)
            self.download_dir.mkdir(exist_ok=True)
        else:
            self.download_dir = base_dir / "downloads"/ Path(platform_config_path).stem

        self._chat_groups = None # 对话分组


    async def check_auth_valid(self, browser: Browser):
        """检查认证是否过期"""
        # 加载认证状态
        if self.auth_state_path.exists():
            logging.info(f"尝试用认证状态: {self.auth_state_path} 进行登录...")
            context = await browser.new_context(storage_state=str(self.auth_state_path),
                                                accept_downloads=True)
        else:
            context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await page.goto(self.config.base_url)
        # 等待登录成功指示器
        indicator = self.login_config.indicator_selector
        if not indicator:
            raise ValueError("未指定登录成功指示器")
        try:
            await page.wait_for_selector(indicator, timeout=self.login_config.check_timeout)
            logging.info("登录成功!")
        except TimeoutError:
            logging.info("登录失败, 可能是auth状态过期, 尝试重新登录...")
            await self.login_and_save_state(context, page)

        return context, page


    async def login_and_save_state(self, context: BrowserContext, page: Page):
        """登录并保存认证状态"""
        logging.info("进入登录认证环节...")
        if self.login_config.mode == "manual":
            logging.info(f"请在浏览器中登录 {self.platform_name}...")
            # 等待登录成功指示器
            indicator = self.login_config.indicator_selector
            if not indicator:
                raise ValueError("未指定登录成功指示器")
            try:
                await page.wait_for_selector(indicator, timeout=self.login_config.op_timeout)
            except TimeoutError:
                logging.info("未在指定时间内完成登录, 请重试...")
        elif self.login_config.mode == "auto":
            logging.info("正在自动登录...")
            # TODO 自动登录
        else:
            raise ValueError("未定义的登录模式")
        storage = await context.storage_state()
        self.auth_state_path.parent.mkdir(exist_ok=True)
        with open(self.auth_state_path, "w", encoding="utf-8") as f:
            json.dump(storage, f, ensure_ascii=False, indent=2)
        logging.info(f"认证状态已保存至 {self.auth_state_path}")


    async def get_groups(self, page: Page):
        """获取所有对话分组"""
        if self._chat_groups is None:
            # 等待分组渲染
            await page.wait_for_selector(self.config.conversation.group_container_selector,
                                         timeout=self.config.conversation.load_sidebar_timeout)
            self._chat_groups = await page.query_selector_all(self.config.conversation.group_container_selector)
        return self._chat_groups


    async def close_group_drag(self, page: Page):
        """
        关闭分组的拖拽状态
        :param page:
        :return:
        """
        # 1.获取所有分组
        groups = await self.get_groups(page)
        # 2.关闭分组的拖拽状态
        for group in groups:
            status = await group.query_selector(self.config.conversation.group_status_selector)
            class_names = await status.get_attribute("class")
            if self.config.conversation.group_open_status in class_names:
                # 关闭分组
                await status.click()


    async def export_group_conversations(self, page: Page, group: ElementHandle):
        """
        导出某个分组下的所有对话
        :param group:
        :param page:
        :return:
        """
        # 检测分组下拉状态
        group_drag = await group.query_selector(self.config.conversation.group_drag_selector)
        group_name = await group_drag.text_content()
        group_name = group_name.strip() # 去除空格
        status = await group_drag.query_selector(self.config.conversation.group_status_selector)
        class_names = await status.get_attribute("class")
        if self.config.conversation.group_close_status in class_names:
            # 打开分组
            await status.click()
        # 等待下拉列表加载
        await group.wait_for_selector(self.config.conversation.group_item_selector)
        items = await group.query_selector_all(self.config.conversation.group_item_selector)
        if items:
            await self.perform_export(page, items, group_name)
        else:
            logging.info(f"分组 {group_name} 下没有对话")
            return
        # 重新收起分组
        if self.config.conversation.group_open_status in class_names:
            await status.click()


    async def export_all_groups(self, page: Page):
        """
        导出所有分组分支下的对话记录
        :param page:
        :return:
        """

        chat_groups = await self.get_groups(page)
        for group in chat_groups:
            await self.export_group_conversations(page, group)

    async def export_all_conversations(self):
        """导出所有对话"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            # 检查登录状态
            context, page = await self.check_auth_valid(browser)

            conversation_config = self.config.conversation
            # 导出被分组的对话记录
            # await self.export_all_groups(page)
            # # 收起分组下拉框
            # await self.close_group_drag(page)
            # 导出未分组的对话记录
            await page.wait_for_selector(conversation_config.item_selector)
            items = await page.query_selector_all(conversation_config.item_selector)
            await self.perform_export(page, items)
            await context.close()
            await browser.close()

    async def export_conversation(self, index: int):
        """导出单个对话（调用子类实现具体点击逻辑）"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
            )
            # 检查登录状态
            context, page = await self.check_auth_valid(browser)
            conversation_config = self.config.conversation
            if not conversation_config.sidebar_container:
                raise ValueError("对话侧边栏容器不能为空")
            try:
                await page.wait_for_selector(conversation_config.sidebar_container,
                                             timeout=conversation_config.load_sidebar_timeout)
            except TimeoutError:
                logging.info("未找到对话容器,请检查是否被折叠,或者名称是否有误")
            # 关闭分组下拉框避免影响独立对话的获取
            await self.close_group_drag(page)
            # 等待对话可见否则后续查找到的元素个数是0
            await page.wait_for_selector(conversation_config.item_selector, state="visible")
            conversation_items = await page.query_selector_all(conversation_config.item_selector)
            if index >= len(conversation_items):
                raise IndexError(f"对话索引 {index} 超出范围（共 {len(conversation_items)} 个）")

            await self.perform_export(page, [conversation_items[index]])

            await context.close()
            await browser.close()

    @abstractmethod
    async def _perform_export(self, page: Page) -> Download:
        """
        子类实现：执行点击菜单、选择 JSON 导出等操作，并返回 download 对象
        必须通过 `async with page.expect_download() as dl: ...; return await dl.value`
        """
        pass

    async def perform_export(self, page: Page, items: List[ElementHandle], group_name: str = None) -> None:
        """
        遍历对话列表执行执行点击菜单、选择 JSON 导出等操作
        :param group_name: 分组名
        :param page:
        :param items: 侧边栏对话js对象集合
        :return:
        """
        for chat_item in items:
            await chat_item.click()
            download = await self._perform_export(page)
            title = await chat_item.text_content()

            final_path = self.download_dir
            if group_name is not None:
                # 建立分组目录
                final_path = self.download_dir / group_name
                final_path.mkdir(exist_ok=True)
            final_path = final_path / f"chat_{title.strip()}.json"

            await download.save_as(final_path)
            logging.info(f"✅ 导出成功: {final_path}")