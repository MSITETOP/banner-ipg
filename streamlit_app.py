import os
import streamlit as st
from openai import OpenAI
import json
import random
import requests
import time
from base64 import b64decode

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
seed = random.randint(1000000, 9999999)

st.set_page_config(page_title="AI генерация баннеров",layout="wide")

def create_prompt(txt):
    response = client.chat.completions.create(
        model="o1-mini",
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": f"Ты опытный пользователей нейросетей для генерации изображений. твоя задача придумать запрос для генерации баннера по статье ниже. придумай сцену, выбери объекты, композицию, расставь акценты, стиль, освещение. Будь очень краток максимум 60 слов. отвечай на Английском.\n\nСТАТЬЯ:\n{txt}"
                }
            ]
            }
        ]
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content[:500]

def getImage(prompt, w, h, s):
    print(["промпт", prompt])
    # Замените <значение_IAM-токена> на ваш реальный токен
    HEADERS = {
        "Authorization": f"Api-Key {st.secrets['yandex_key']}", #f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }

    # Параметры для генерации изображения
    request_data = {
        "modelUri": f"art://{st.secrets['folder_id']}/yandex-art/latest",
        "generationOptions": {
            "seed": s,
            "aspectRatio": {
                "widthRatio": w,
                "heightRatio": h
            }
        },
        "messages": [
            {
                "weight": "1",
                "text": prompt
            }
        ]
    }

    # URL для генерации изображения
    generate_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"

    # Отправляем запрос на генерацию изображения
    response = requests.post(generate_url, headers=HEADERS, json=request_data)

    if response.status_code == 200:
        # Получаем ID запроса из ответа
        request_id = response.json().get('id')
        print(f"Запрос на генерацию отправлен, ID запроса: {request_id}")
    else:
        print(f"Ошибка при отправке запроса: {response.status_code}, {response.text}")
        return False
        
    while True:
        time.sleep(1)    
        # URL для проверки статуса генерации
        status_url = f"https://llm.api.cloud.yandex.net:443/operations/{request_id}"
        # Отправляем GET запрос для получения результата
        result_response = requests.get(status_url, headers=HEADERS)
        if result_response.status_code == 200:
            # Проверяем, готово ли изображение
            result_data = result_response.json()
            if result_data.get('done'):
                # Если готово, извлекаем изображение в формате Base64
                return result_data.get('response', {}).get('image')
            else:
                print("Изображение еще не готово. Попробуйте позже.")
        else:
            print(f"Ошибка при получении результата: {result_response.status_code}, {result_response.text}")
    return False


txt = st.text_area(label="Текст статьи для генерации промпта", value="")
prompt_txt = ""

if st.button("Создать промпт"):
    prompt_txt = create_prompt(txt)

seed = st.text_input(label="Зерно (seed) — это число, на основе которого будет происходить генерация изображения. Вы можете сами указать число или задать случайное значение. При одинаковых промте и зерне результаты генераций будут одинаковыми.", value=seed)
prompt_txt = st.text_area(label="Полученный промпт (его можно отредактировать перед генерацией)", max_chars=500, value=prompt_txt)

if st.button("Создать баннер 1920х400"):
    i = getImage(prompt_txt, 1920, 400, seed)
    st.html(f"<img src='data:image/jpeg;base64,{i}'>")
if st.button("Создать баннер 400х800"):
    i = getImage(prompt_txt, 400, 800, seed)
    st.html(f"<img src='data:image/jpeg;base64,{i}'>")
if st.button("Создать баннер 400х400"):
    i = getImage(prompt_txt, 400, 400, seed)
    st.html(f"<img src='data:image/jpeg;base64,{i}'>")