import asyncio
import logging
import re
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Константы для парсинга
BASE_URL = "https://music.yandex.ru"
START_URL = f"{BASE_URL}/new-playlists"
PLAYLISTS_JSON_FILE = "playlists_data.json"
ARTISTS_JSON_FILE = "artists_data.json"

# Настройки прокси
PROXY_SERVER = "http://91.147.123.170:49155"  # Обновлено: убраны креденшелы из URL
PROXY_USERNAME = "m48UiPm5"
PROXY_PASSWORD = "xMzzx6c5aj"

class YandexMusicParser:
    def __init__(self):
        self.playlists_data = []
        self.artists_data = []
        self.artists_urls = set()
        self.sem = asyncio.Semaphore(3)  # Ограничиваем до 3 одновременных запросов

    async def save_to_json(self, data, file_path):
        """Сохраняет данные в JSON файл."""
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info(f"Данные сохранены в {file_path}")

    async def fetch_page(self, page, url, scroll=False):
        """Загружает страницу с помощью Playwright."""
        async with self.sem:
            await page.goto(url)
            await asyncio.sleep(10)  # Ждем загрузки страницы

            if scroll:
                # Эмулируем скроллинг страницы до конца
                previous_height = None
                while True:
                    current_height = await page.evaluate('document.body.scrollHeight')
                    if previous_height == current_height:
                        break
                    previous_height = current_height
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(3)

            content = await page.content()
            logging.info(f"Успешно загружено: {url}")
            return content

    async def parse_playlists(self, html):
        """Извлекает информацию о плейлистах со страницы."""
        soup = BeautifulSoup(html, 'lxml')
        playlists = soup.select("div.playlist__title a.deco-link")
        logging.info(f"Найдено плейлистов: {len(playlists)}")

        for playlist in playlists:
            title = playlist.get_text(strip=True)
            playlist_url = BASE_URL + playlist['href']

            playlist_info = {
                "title": title,
                "url": playlist_url
            }
            self.playlists_data.append(playlist_info)
            logging.info(f"Найден плейлист: {title} - {playlist_url}")

    async def parse_artists_from_playlist(self, playlist_url, browser):
        """Извлекает исполнителей из плейлиста и сохраняет их сразу в JSON-файл."""
        page = await browser.new_page()
        html = await self.fetch_page(page, playlist_url)
        soup = BeautifulSoup(html, 'lxml')
        tracks = soup.select("div.d-track")
        logging.info(f"Найдено треков в плейлисте: {len(tracks)}")

        tasks = []

        for track in tracks:
            artist_elements = track.select("span.d-track__artists a")
            for artist_element in artist_elements:
                artist_name = artist_element.text.strip()
                artist_url = BASE_URL + artist_element['href']

                if artist_url in self.artists_urls:
                    continue  # Артист уже обработан

                self.artists_urls.add(artist_url)
                tasks.append(self.fetch_listeners_from_artist_page(artist_name, artist_url, browser))

        # Параллельно выполняем запросы к страницам артистов (с учетом ограничения семафора)
        await asyncio.gather(*tasks)
        await page.close()

    async def fetch_listeners_from_artist_page(self, artist_name, artist_url, browser):
        """Парсит количество слушателей на странице исполнителя."""
        async with self.sem:
            try:
                page = await browser.new_page()
                await page.goto(artist_url)
                await page.wait_for_selector("div.page-artist__summary", timeout=10000)
                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')
                listeners_element = soup.select_one("div.page-artist__summary")
                if listeners_element:
                    listeners_text = listeners_element.get_text(strip=True).replace(" ", "")
                    match = re.search(r'(\d+)', listeners_text)
                    if match:
                        listeners = int(match.group(1))
                        artist_info = {
                            "artist": artist_name,
                            "listeners": listeners,
                            "url": artist_url
                        }
                        self.artists_data.append(artist_info)
                        logging.info(f"Найден артист: {artist_name} с {listeners} слушателями")
                        # Сохраняем данные
                        await self.save_to_json(self.artists_data, ARTISTS_JSON_FILE)
                await page.close()
            except Exception as e:
                logging.error(f"Ошибка при загрузке страницы артиста {artist_url}: {e}")

    async def run(self):
        """Основной метод для запуска парсера."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, proxy={
                "server": PROXY_SERVER,
                "username": PROXY_USERNAME,
                "password": PROXY_PASSWORD
            })  # Передаем настройки прокси при запуске браузера

            page = await browser.new_page()

            # Получаем HTML главной страницы с плейлистами
            html = await self.fetch_page(page, START_URL, scroll=True)
            if not html:
                logging.error("Не удалось загрузить стартовую страницу")
                await browser.close()
                return

            # Парсим плейлисты
            await self.parse_playlists(html)
            if not self.playlists_data:
                logging.error("Не удалось найти плейлисты")
                await browser.close()
                return
            await self.save_to_json(self.playlists_data, PLAYLISTS_JSON_FILE)

            # Обрабатываем плейлисты последовательно или параллельно с учетом ограничения
            for playlist in self.playlists_data:
                logging.info(f"Переход к плейлисту: {playlist['title']} - {playlist['url']}")
                await self.parse_artists_from_playlist(playlist['url'], browser)

            await browser.close()

if __name__ == "__main__":
    parser = YandexMusicParser()
    asyncio.run(parser.run())
