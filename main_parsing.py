import pandas as pd
from bs4 import BeautifulSoup
import csv
from processing import Processing

pr = Processing()

output_file = "output_test.csv"

def parsing(data, first=True):
    # Проходим по каждой странице
    counter_page = 0
    errors_page = []
    # Итоговый массив для сохранения в csv
    results = []
    for row in data[['url', 'html']].itertuples(index=False):
        url, text = row.url, row.html
        try:
            soup = BeautifulSoup(text, 'html.parser')

            # Извлечение всех json скриптов
            js_scripts = soup.find_all('script', type='application/ld+json')
            emails, phones, names, social_media, addresses = [], [], [], [], []

            # Извлекаем информацию из json скриптов
            phones, emails, addresses = pr.js_scanning(js_scripts, phones=phones, emails=emails, addresses=addresses)

            # Обработка ссылок - DeepPavlov
            social_media, phones, emails, addresses, names = pr.a_href_scanning(soup, social_media, phones, emails,
                                                                                addresses, names)

            # Обработка текста страницы + DeepPavlov
            page_text = soup.get_text(separator=' ', strip=True)
            phones, emails, names, addresses = pr.page_text_scanning(page_text, phones, emails, names, addresses)

            # Убираем дубликаты
            social_media = list(set(social_media))
            phones = list(set(phone.strip() for phone in phones if phone.strip()))
            emails = list(set(email.strip() for email in emails if email.strip()))

            final_phones = pr.last_four_digits(phones)

            results.append({
                "url": url,
                "emails": ";".join(emails) if emails else None,
                "phones": ";".join(final_phones) if final_phones else None,
                "links_social_media": ";".join(social_media) if social_media else None,
                "addresses": ";".join(addresses) if addresses else None,
                "names": ";".join(names) if names else None
            })
        except Exception as e: # Обработка ошибок отдельных страниц
            errors_page.append([e, counter_page]) 

        counter_page += 1

    mode = 'w' if first else 'a'
    # Запись в CSV
    with open(output_file, mode, newline='', encoding='utf-8') as file:
        fieldnames = ["url", "names", "emails", "phones", "links_social_media", "addresses"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if first:
            writer.writeheader()

        for row in results:
            writer.writerow(row)

    return errors_page

errors = []
for i in range(pr.n_for_range):

    start, stop = i * pr.step, (i+1) * pr.step
    print(start, stop)
    try:
        data = pd.read_csv(f'pieces/piece_{start}_{stop}.csv')
        errors_page = parsing(data, first = (i==0))
        errors.extend(errors_page)

    except Exception as e:
        errors.append([e, f"Номер piece{i}"])


print(f"Список ошибок {errors}")