import os
import streamlit as st
from openai import OpenAI
import json
import random
import requests
import time
from base64 import b64decode

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if st.session_state.get("seed", False): 
    seed = st.session_state["seed"]
else:
    seed = random.randint(10000000, 99999999)
    st.session_state["seed"] = seed

if st.session_state.get("prompt_txt", False): 
    prompt_txt = st.session_state["prompt_txt"]
else:
    prompt_txt = ""
    st.session_state["prompt_txt"] = prompt_txt

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
                "text": f"Ты опытный пользователей нейросетей для генерации изображений. твоя задача придумать запрос для генерации баннера по статье ниже. придумай сцену, выбери объекты, композицию, расставь акценты, стиль, освещение. Будь очень краток максимум 70 слов.\n\nСТАТЬЯ:\n{txt}"
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

def getImageDalle(prompt, w, h, quality = "standard"):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=f"{w}x{h}",
        quality=quality,
        n=1,
    )
    return response.data[0].url


txt = st.text_area(label="Текст статьи для генерации промпта", value="")

if st.button("Создать промпт"):
    prompt_txt = create_prompt(txt)
    st.session_state["prompt_txt"] = prompt_txt

seed = st.text_input(label="Зерно (seed) — это число, на основе которого будет происходить генерация изображения. При одинаковых промте и зерне результаты генераций будут одинаковыми.", value=seed)
st.session_state["seed"] = seed

prompt_txt = st.text_area(label="Полученный промпт (его можно отредактировать перед генерацией)", max_chars=500, value=prompt_txt)
st.session_state["prompt_txt"] = prompt_txt

col1, col2, col3 = st.columns(3)
with col1:
    btn1 = st.button("Создать баннер 2560х500")
    btn2 = st.button("Создать баннер 400х800")
    btn3 = st.button("Создать баннер 400х400")

with col2:
    btn4 = st.button("Создать баннер DALLE 2560х500")
    btn5 = st.button("Создать баннер DALLE 400х800")
    btn6 = st.button("Создать баннер DALLE 400х400")

with col3:
    btn7 = st.button("Создать баннер DALLE HD 2560х500")
    btn8 = st.button("Создать баннер DALLE HD 400х800")
    btn9 = st.button("Создать баннер DALLE HD 400х400")

if btn1:
    i1 = getImage(prompt_txt, 2560, 500, seed)
    st.html(f"<img style='max-width: 100%;' src='data:image/jpeg;base64,{i1}'>")
if btn2:
    i2 = getImage(prompt_txt, 400, 800, seed)
    st.html(f"<img style='max-width: 100%;' src='data:image/jpeg;base64,{i2}'>")
if btn3:
    i3 = getImage(prompt_txt, 400, 400, seed)
    st.html(f"<img style='max-width: 100%;' src='data:image/jpeg;base64,{i3}'>")
if btn4:
    i1 = getImageDalle(prompt_txt, 1792, 1024)
    st.html(f"<img style='max-width: 100%;' src='{i1}'>")
if btn5:
    i2 = getImageDalle(prompt_txt, 1024, 1792)
    st.html(f"<img style='max-width: 100%;' src='{i2}'>")
if btn6:
    i3 = getImageDalle(prompt_txt, 1024, 1024)
    st.html(f"<img style='max-width: 100%;' src='{i3}'>")
if btn7:
    i1 = getImageDalle(prompt_txt, 1792, 1024, "hd")
    st.html(f"<img style='max-width: 100%;' src='{i1}'>")
if btn8:
    i2 = getImageDalle(prompt_txt, 1024, 1792, "hd")
    st.html(f"<img style='max-width: 100%;' src='{i2}'>")
if btn9:
    i3 = getImageDalle(prompt_txt, 1024, 1024, "hd")
    st.html(f"<img style='max-width: 100%;' src='{i3}'>")

