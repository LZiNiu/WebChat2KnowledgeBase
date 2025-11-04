import asyncio
import logging
from typing import Dict

from .base_crawler import ExportCrawler
from playwright.async_api import Page, Download


class QwenExportCrawler(ExportCrawler):
    async def _perform_export(self, page: Page) -> Download:
        export_config = self.config.export

        # 1. 点击导出触发按钮
        trigger_sel = export_config.trigger_button_selector
        menu_button = await page.wait_for_selector(trigger_sel, timeout=export_config.timeout)
        await menu_button.click()
        print("已点击导出菜单按钮")

        # 2. 等待菜单项
        menu_item_sel = export_config.menu_item_selector
        await page.wait_for_selector(menu_item_sel, timeout=export_config.timeout)
        menu_items = await page.query_selector_all(menu_item_sel)

        # 3. 查找主“下载/导出”项
        main_keywords = export_config.main_export_keywords
        main_item = None
        for item in menu_items:
            text = await item.text_content()
            if text:
                text = text.strip()
                if any(kw in text for kw in main_keywords):
                    main_item = item
                    print(f"找到主菜单项: {text}")
                    break
        if not main_item:
            raise RuntimeError(f"未找到主导出菜单项，关键词: {main_keywords}")

        # 4. 是否 hover 触发子菜单？
        if export_config.trigger_mode == "hover":
            await main_item.hover()
        else:
            await main_item.click()
        # 等待子菜单出现
        cnt = 0
        sub_menu_items = None
        while cnt < 2:
            # 至多尝试 2 次
            await asyncio.sleep(0.1)
            new_menu_items = await page.query_selector_all(menu_item_sel)
            if len(new_menu_items) > len(menu_items):
                sub_menu_items = new_menu_items[len(menu_items):]
                logging.info(f"已找到子菜单项 {len(sub_menu_items)} 个")
                break
        if not sub_menu_items:
            raise RuntimeError("未找到子菜单项")
        # 5. 查找“导出为 JSON”子项（如有）
        json_keywords = export_config.json_export_keywords
        if json_keywords:
            json_item = None
            for item in sub_menu_items:
                text = await item.text_content()
                if text:
                    text = text.strip()
                    if any(kw in text for kw in json_keywords):
                        json_item = item
                        print(f"找到 JSON 导出项: {text}")
                        break
            if not json_item:
                raise RuntimeError(f"未找到 JSON 导出子菜单项，关键词: {json_keywords}")

            # 触发下载
            async with page.expect_download() as download_info:
                await json_item.click()
            return await download_info.value

        else:
            # 无子菜单：点击主项即下载
            async with page.expect_download() as download_info:
                # 如果前面已点击主项触发了下载，expect_download 会捕获它
                # 无需额外操作，但确保上下文处于下载监听状态
                pass
            return await download_info.value