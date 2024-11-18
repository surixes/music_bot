import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import time
import random
import logging
import re
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройки для заголовков
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}

# Константы для парсинга
BASE_URL = "https://music.yandex.ru"
START_URL = f"{BASE_URL}/new-playlists"
PLAYLISTS_JSON_FILE = "playlists_data.json"
ARTISTS_JSON_FILE = "artists_data.json"

class YandexMusicParser:
    def __init__(self, start_url):
        self.start_url = start_url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.playlists_data = self.load_existing_data(PLAYLISTS_JSON_FILE)
        self.artists_data = self.load_existing_data(ARTISTS_JSON_FILE)

    def load_existing_data(self, file_path):
        """Загружает существующие данные из JSON файла, если он существует."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                logging.error(f"Ошибка при загрузке JSON файла: {file_path}")
                return []
        return []

    def save_to_json(self, data, file_path):
        """Сохраняет данные в JSON файл."""
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info(f"Данные сохранены в {file_path}")

    def fetch_page_with_selenium(self, url):
        """Получает HTML-страницу по URL с помощью Selenium."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            time.sleep(10)  # Ожидание загрузки страницы

            html = driver.page_source

            # Сохраняем HTML-код в файл для анализа
            with open("fetched_page.html", "w", encoding="utf-8") as file:
                file.write(html)

            driver.quit()
            logging.info(f"Успешно загружено с помощью Selenium: {url}")
            return html
        except Exception as e:
            logging.error(f"Ошибка при загрузке {url} с помощью Selenium: {e}", exc_info=True)
            return None

    def parse_playlists(self, html):
        """Извлекает информацию о плейлистах со страницы."""
        soup = BeautifulSoup(html, 'html.parser')
        playlists = soup.select("div.gallery__items div.gallery__item a.d-link")  # Обновите селектор согласно структуре
        logging.info(f"Найдено элементов плейлистов: {len(playlists)}")
        playlist_data = []

        for playlist in playlists:
            title = playlist.get('title', '').strip()
            playlist_url = BASE_URL + playlist['href']
            
            playlist_info = {
                "title": title,
                "url": playlist_url
            }
            playlist_data.append(playlist_info)
            logging.info(f"Найден плейлист: {title} - {playlist_url}")

        return playlist_data

    def fetch_all_artists_from_playlist(self, html):
        """Извлекает всех исполнителей из каждого трека плейлиста."""
        soup = BeautifulSoup(html, 'html.parser')
        tracks = soup.select("div.d-track")  # Обновите селектор согласно структуре
        logging.info(f"Найдено треков: {len(tracks)}")
        artists_data = []

        for track in tracks:
            artist_elements = track.select("a.d-track__artists")
            for artist_element in artist_elements:
                artist_name = artist_element.text.strip()
                artist_url = BASE_URL + artist_element['href']

                # Проверяем, не парсили ли мы уже этого артиста
                if any(artist['url'] == artist_url for artist in self.artists_data):
                    continue

                # Получаем количество слушателей
                listeners = self.fetch_listeners_from_artist_page(artist_url)
                if listeners is not None:
                    artist_info = {
                        "artist": artist_name,
                        "listeners": listeners,
                        "url": artist_url
                    }
                    artists_data.append(artist_info)
                    self.artists_data.append(artist_info)
                    logging.info(f"Найден артист: {artist_name} с {listeners} слушателей")

        return artists_data

    def fetch_listeners_from_artist_page(self, artist_url):
        """Парсит количество слушателей на странице исполнителя с помощью Selenium."""
        html = self.fetch_page_with_selenium(artist_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        listeners_element = soup.select_one("span.page-artist__listeners")  # Обновите селектор согласно структуре
        if listeners_element:
            listeners_text = listeners_element.text.replace(" ", "")
            match = re.search(r'\d+', listeners_text)
            if match:
                return int(match.group())
        logging.error(f"Не удалось найти количество слушателей на странице {artist_url}")
        return None

    def run(self):
        """Основной метод для запуска парсера."""
        html = self.fetch_page_with_selenium(self.start_url)
        if not html:
            logging.error("Не удалось загрузить стартовую страницу")
            return

        # Парсинг плейлистов
        playlists = self.parse_playlists(html)
        if not playlists:
            logging.error("Не удалось найти плейлисты")
            return
        self.save_to_json(playlists, PLAYLISTS_JSON_FILE)
        logging.info(f"Найдено плейлистов: {len(playlists)}")

        # Парсинг всех артистов из плейлистов
        for playlist in playlists:
            if playlist['url']:
                time.sleep(random.uniform(1, 3))
                logging.info(f"Переход к плейлисту: {playlist['title']} - {playlist['url']}")

                # Используем Selenium для загрузки страницы плейлиста
                playlist_html = self.fetch_page_with_selenium(playlist['url'])
                if playlist_html:
                    artists = self.fetch_all_artists_from_playlist(playlist_html)
                    if artists:
                        self.save_to_json(self.artists_data, ARTISTS_JSON_FILE)

if __name__ == "__main__":
    parser = YandexMusicParser(START_URL)
    parser.run()
