import re
import json
from pavlov_deep import Pavlov_Deep

pavlov = Pavlov_Deep()
class Processing():

    def __init__(self):
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'(?<!\d)(\+7|8)[\s\-]?\(?\d{3,4}\)?[\s\-]?\d{2,3}[\s\-]?\d{2}[\s\-]?\d{2,4}(?!\d)')
        self.n_for_range = 20 
        self.step = 500 # Шаг разбиения файла
        self.social_media_links = ['https://vk.com/', 'https://wa.me', 'viber://chat', 'https://t.me/', 'https://ok.ru/',
                           'skype:', 'https://www.youtube.com/']
        self.text_href = []

    def js_scanning(self, js_scripts, phones, emails, addresses):
        def extract_data(json_obj, phones, emails, addresses):
            # Извлекаем телефоны
            phone_json = json_obj.get('telephone', [])
            if isinstance(phone_json, str):
                phones.append(phone_json)
            elif isinstance(phone_json, list):
                phones.extend(phone_json)

            # Извлекаем email
            email_json = json_obj.get('email', [])
            if isinstance(email_json, str):
                emails.append(email_json)
            elif isinstance(email_json, list):
                emails.extend(email_json)

            # Извлекаем адреса
            address_json = json_obj.get('address', [])
            if isinstance(address_json, dict):
                addresses.append(
                    f"{address_json.get('streetAddress', '')}, {address_json.get('addressLocality', '')}, {address_json.get('addressRegion', '')}, {address_json.get('postalCode', '')}".strip(
                        ", ")
                )

        # Обработка JSON-LD скриптов
        for script in js_scripts:
            try:
                if script.string:
                    json_data = json.loads(script.string)
                    if type(json_data) is list: # Обрабатываем список
                        for item in json_data:
                            if isinstance(item, dict):
                                extract_data(item, phones, emails, addresses)
                    elif type(json_data) is dict: # Обрабатываем словарь
                        extract_data(json_data, phones, emails, addresses)
            except json.JSONDecodeError:
                continue

        return phones, emails, addresses

    def a_href_scanning(self, soup, social_media, phones, emails, addresses, names):
        for link in soup.find_all('a', href=True):
            self.text_href.append(link.get_text(strip=True))  # Извлечение текста из ссылок
            # Ищем информацию о соц-медиа, телефонах, emails
            if any(link['href'].startswith(so_me) for so_me in self.social_media_links):
                so_me = link['href'].strip()
                social_media.append(so_me)
            elif link['href'].startswith('tel:'):
                phone = link['href'].replace('tel:', '').strip()
                phones.append(phone)
            elif link['href'].startswith('mailto:'):
                email = link['href'].replace('mailto:', '').strip()
                emails.append(email)

        re_for_address = ['д.', 'микрорайон', 'улица', 'ул.', 'стр.', 'офис', 'шоссе', 'ш.', 'пер.', 'проспект', 'пр-т']

        address_pattern = re.compile(r'.'.join([fr'\b{kw}\b' for kw in re_for_address]))

        # Ищем совпадения в ссылках
        for i in self.text_href:
            if address_pattern.search(i):
                addresses.append(i)
            if self.phone_pattern.search(i):
                phones.append(i)

        # # Нейронка Павлов
        # names, addresses = pavlov.pavlov_scanning(text=self.text_href, names=names, addresses=addresses, list_= True)

        return social_media, phones, emails, addresses, names

    def page_text_scanning(self, page_text, phones, emails, names, addresses):
        print("Проверка текста страницы")
        print(page_text)
        if type(page_text) is str:

            # Нейронка Павлов
            names, addresses = pavlov.pavlov_scanning(text = page_text, names= names, addresses= addresses)

            phones_ = self.phone_pattern.finditer(page_text) # Работа с регулярным выражением
            for phone in phones_:
                match = phone.group()
                if match not in phones:
                    phones.append(match)
            emails_ = self.email_pattern.finditer(page_text)
            for email in emails_:
                match = email.group()
                if match not in emails:
                    emails.append(match)
        elif type(page_text) is list:
            for piece_page_text in page_text:

                # Нейронка Павлов
                names, addresses = pavlov.pavlov_scanning(text = piece_page_text, names= names, addresses= addresses, list_=True)

                phones_ = self.phone_pattern.finditer(piece_page_text)
                for phone in phones_:
                    match = phone.group()
                    if match not in phones:
                        phones.append(match)
                emails_ = self.email_pattern.finditer(piece_page_text)
                for email in emails_:
                    match = email.group()
                    if match not in emails:
                        emails.append(match)

        return phones, emails, names, addresses

    def last_four_digits(self, phones):
        # Регулярка для извлечения последних 4 цифр номера
        last_four_digits_pattern = re.compile(r'(\d{4})$')

        final_phones = []
        unique_last_four = set()  # Множество для отслеживания уникальных последних 4 цифр
        for phone in phones:
            match = last_four_digits_pattern.search(
                re.sub(r'\D', '', phone))
            if match:
                last_four_digits = match.group(1)

                if last_four_digits not in unique_last_four and len(phone) < 18:
                    unique_last_four.add(last_four_digits)
                    final_phones.append(phone)

        return final_phones