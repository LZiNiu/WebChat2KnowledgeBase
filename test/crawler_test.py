# run.py
import asyncio
from pathlib import Path

from CrawlBrowser.crawlers.base_crawler import ExportCrawler
from CrawlBrowser.crawlers.crawlers import QwenExportCrawler


# 简单工厂（可根据平台名扩展）
CRAWLER_MAP: dict[str, type[ExportCrawler]] = {
    "qwen": QwenExportCrawler,
    # "kimi": KimiExportCrawler,
}

async def main():
    platform = "qwen"
    index = 0
    if platform not in CRAWLER_MAP:
        raise ValueError(f"不支持的平台: {platform}")

    crawler_class = CRAWLER_MAP[platform]
    crawler_config_path = Path(__file__).parent.parent / "CrawlBrowser" / "platforms" / f"{platform}.yml"
    crawler = crawler_class(crawler_config_path)
    await crawler.export_all_conversations()
if __name__ == "__main__":
    asyncio.run(main())
