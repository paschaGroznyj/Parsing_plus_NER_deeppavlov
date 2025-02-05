from deeppavlov import configs, build_model
import torch
import json
import re

# Проверяем доступность GPU
if not torch.cuda.is_available():
    print("GPU не доступен, используется CPU.")
# Загружаем модель NER
try:
    ner_model = build_model(configs.ner.ner_rus_bert)
except Exception as e:
    print(f"Ошибка загрузки модели: {e}")
    exit()

class Pavlov_Deep:

    def split_text(self, text, max_tokens=300, list_=False):

        parts = []
        # Убираем фрагменты JSON
        try:
            json_part = re.search(r'{.*}', text, re.DOTALL)
            if json_part:
                json_content = json_part.group()
                # Убираем JSON из текста для дальнейшего разбиения
                text = text.replace(json_content, '')
                parsed_json = json.loads(json_content)
                parts.append(f"JSON: {json.dumps(parsed_json, indent=2)}")
        except Exception as e:
            print(f"Ошибка обработки JSON: {e}")

        if not text:
            return []

        split_sentences = []

        if not list_:
            sentences = re.split(r'(?<=[.!?;*")])\s+', text) # Разбиваем текст на предложения
        else:
            text = ' '.join([t.strip() for t in text if t.strip()])  # Убираем пустые строки
            sentences = re.split(r'(?<=[.!?;*")])\s+', text)

        # Разбиваем предложения на части
        for sentence in sentences:
            words = sentence.split()
            while len(words) > max_tokens:
                split_sentences.append(" ".join(words[:max_tokens]))
                words = words[max_tokens:]
            if words:
                split_sentences.append(" ".join(words))
            elif sentence.strip():
                split_sentences.append(sentence.strip())

        return split_sentences


    def pavlov_scanning(self, text, names, addresses, list_ = False):
        if not list_:
            sentences_text = self.split_text(text) # Разбиваем текст
        else:
            sentences_text = self.split_text(text, list_ = True)

        for i, piece in enumerate(sentences_text):
            print(f"Номер прогона {i}")
            print(piece)
            # Подача текста в модель
            result = ner_model([piece[0:510]])  # На всякий случай срежем лишнее

            for tokens, categories in zip(result[0], result[1]):
                current_name = [] # Стек для B-Per + I-Per
                current_address = [] # Стек для B-Loc + I-Loc

                for token, category in zip(tokens, categories):
                    # Обработка имен
                    if category == 'B-PER':
                        if current_name:
                            names.append(" ".join(current_name))
                        current_name = [token]
                    elif category == 'I-PER':
                        current_name.append(token)
                    elif current_name:
                        names.append(" ".join(current_name))
                        current_name = []

                    # Обработка адресов
                    if category == 'B-LOC':
                        if current_address:
                            addresses.append(" ".join(current_address))
                        current_address = [token]
                    elif category == 'I-LOC':
                        current_address.append(token)
                    elif current_address:
                        addresses.append(" ".join(current_address))
                        current_address = []

                # Добавляем оставшееся 
                if current_name:
                    names.append(" ".join(current_name))
                if current_address:
                    addresses.append(" ".join(current_address))


        # Убираем дубликаты
        return list(set(names)), list(set(addresses))
