import logging
import aiohttp

class TerminalCreator:
    def __init__(self, name, login, mac, hall_id, api_url):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.name = name
        self.login = login
        self.mac = mac
        self.hall_id = hall_id
        self.url = api_url

    async def create_terminal(self):
        data = {
            "cmd": "terminalCreate",
            "name": self.name,
            "login": self.login,
            "mac": self.mac,
            "hall_id": self.hall_id
        }

        self.logger.info(f"Отправка POST запроса на {self.url} с данными: {data}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=data) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    self.logger.info(f"Код статуса ответа: {response.status}")
                    self.logger.info(f"Ответ JSON: {json_response}")
                    return json_response
        except aiohttp.ClientError as e:
            self.logger.error(f"Запрос не удался: {e}")
            return None
