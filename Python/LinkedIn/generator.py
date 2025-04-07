# generator.py
import os
from openai import OpenAI, OpenAIError, RateLimitError
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_post_variants(title, summary, use_mock=True):
    if use_mock:
        return [
            f"[Факт] {title}: ключевые выводы статьи.",
            f"[Аналитика] Почему это важно: {summary[:100]}...",
            f"[История] Недавно обсуждали похожее — вот краткий взгляд."
        ]

    prompt = f"""
    На основе следующей статьи:
    Заголовок: {title}
    Содержание: {summary}

    Сгенерируй 3 варианта постов для LinkedIn по шаблону:
    1. Фактологичный
    2. Аналитический
    3. История / вовлекающий стиль

    Каждый вариант не более 500 символов.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    content = response.choices[0].message.content.strip()
    return [variant.strip() for variant in content.split("\n\n") if variant.strip()]

def generate_image_prompt(summary, use_mock=False):
    if use_mock:
        return "Графика: минималистичная иллюстрация по теме DevOps или безопасности."

    prompt = f"Создай краткое описание сцены для генерации изображения к посту. Вот текст: {summary}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def check_api_status():
    try:
        test_prompt = "Скажи 'OK', если всё работает."
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.0,
            max_tokens=1
        )
        return {"ok": True}
    except RateLimitError:
        return {"ok": False, "message": "Превышен лимит или недостаточно средств."}
    except OpenAIError as e:
        return {"ok": False, "message": str(e)}
    except Exception as e:
        return {"ok": False, "message": f"Неизвестная ошибка: {e}"}