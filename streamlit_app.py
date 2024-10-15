import os
import io
import streamlit as st
from openai import OpenAI
import json
import random
import requests
import time
from base64 import b64decode, b64encode
from PIL import Image, ImageFilter
from io import BytesIO
import numpy as np

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

if st.session_state.get("image", False): 
    i = st.session_state["image"]
else:
    i = False

st.set_page_config(page_title="AI генерация баннеров",layout="wide")

def create_prompt(txt):
    response = client.chat.completions.create(
        model="gpt-4o-mini", #"o1-mini"
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": f"Ты опытный пользователей нейросетей для генерации изображений. твоя задача придумать запрос для генерации баннера по статье ниже. Будь очень краток максимум 70 слов. отвечай например так 'Сцена: офис строительной компании с командой сотрудников, работающих на компьютерах. Объекты: экран с интерфейсом Битрикс24, строительные планы, каска, ноутбук. Композиция: сотрудники обсуждают проект, на фоне видны строительные материалы. Акцент на взаимодействии и эффективности. Стиль: современный, строгий. Освещение: яркое, дневное, с акцентом на экран.\n\nСТАТЬЯ:\n{txt}"
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
                image_data = b64decode(result_data.get('response', {}).get('image'))
                image_buf = io.BytesIO(image_data)
                return image_buf
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

    response = requests.get(response.data[0].url)
    buf = BytesIO(response.content)
    return buf

def to_base64_image(buf):
    img_str = b64encode(buf.getvalue()).decode("utf-8")   
    return img_str

def img_scale(buf, prompt):
    img = Image.open(buf)
    # Рассчитываем новую ширину с учетом пропорций
    new_height = 400
    aspect_ratio = img.width / img.height
    new_width = int(new_height * aspect_ratio)

    # Изменяем размер изображения
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)

    mask_big = Image.new('RGBA', (1920, 1920), (255, 255, 255, 0))
    mask_big.paste(img_resized, (610, 760))

    mask = mask_big.resize((1024, 1024), Image.LANCZOS)    
    buffered_mask = io.BytesIO()
    mask.save(buffered_mask, format="PNG")
    buffered_mask.seek(0)

    response = client.images.edit(
        model="dall-e-2",
        image=buffered_mask,
        mask=buffered_mask,
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    res = requests.get(response.data[0].url)
    image = Image.open(BytesIO(res.content))
    width, height = image.size

    # Создаем маску градиента
    gradient = np.zeros((height, width), dtype=np.uint8)

    for x in range(width):
        if x < 50 or x > width - 50:
            # Полное размытие
            gradient[:, x] = 255
        elif x < 350:
            # Градиент для первых 50 пикселей
            gradient[:, x] = int(255 * (1 - (x - 50) / 300))
        elif x > width - 350:
            # Градиент для последних 50 пикселей
            gradient[:, x] = int(255 * (1 - (width - x - 50) / 300))

    gradient_mask = Image.fromarray(gradient)

    # Применяем размытие к изображению
    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=5))

    # Смешиваем оригинальное изображение и размазанное с помощью маски
    final_image = Image.composite(blurred_image, image, gradient_mask)

    # Масштабируем изображение до ширины 1920
    final_image = final_image.resize((1920, int(1920 * height / width)), Image.LANCZOS)
    #final_image.paste(img_resized, (610, 760))

    # Обрезаем изображение до высоты 400
    final_image = final_image.crop((0, (final_image.height - 400) // 2, 1920, (final_image.height + 400) // 2))

    # Сохраняем измененное изображение
    buffered = io.BytesIO()
    final_image.save(buffered, format="JPEG") # Или другой формат, который вам нужен
    img_str = b64encode(buffered.getvalue()).decode("utf-8")   

    return img_str


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
    btn1 = st.button("Создать баннер YandexArt 1920x400")
    btn2 = st.button("Создать баннер YandexArt 400х800")
    btn3 = st.button("Создать баннер YandexArt 400х400")

with col2:
    btn4 = st.button("Создать баннер DALLE 1920x400")
    btn5 = st.button("Создать баннер DALLE 400х800")
    btn6 = st.button("Создать баннер DALLE 400х400")

with col3:
    btn7 = st.button("Создать баннер DALLE HD 1920x400")
    btn8 = st.button("Создать баннер DALLE HD 400х800")
    btn9 = st.button("Создать баннер DALLE HD 400х400")

if btn1:
    i = getImage(prompt_txt, 2560, 500, seed)
if btn2:
    i = getImage(prompt_txt, 400, 800, seed)
if btn3:
    i = getImage(prompt_txt, 400, 400, seed)
if btn4:
    i = getImageDalle(prompt_txt, 1792, 1024)
if btn5:
    i = getImageDalle(prompt_txt, 1024, 1792)    
if btn6:
    i = getImageDalle(prompt_txt, 1024, 1024)
if btn7:
    i = getImageDalle(prompt_txt, 1792, 1024, "hd")
if btn8:
    i = getImageDalle(prompt_txt, 1024, 1792, "hd")
if btn9:
    i = getImageDalle(prompt_txt, 1024, 1024, "hd")

if i:
    st.session_state["image"] = i
    st.html(f"<img style='max-width: 100%;' src='data:image/jpeg;base64,{to_base64_image(i)}'>")

col1, col2, col3 = st.columns(3)
with col1:
    w = st.text_input(label="Width", value="1920")
with col2:
    h = st.text_input(label="Height", value="400")
with col3:
    btn10 = st.button("Изменить размеры изображения")
    
if btn10:
    i = img_scale(i, prompt_txt)
    st.html(f"<img style='max-width: 100%;' src='data:image/jpeg;base64,{i}'>")