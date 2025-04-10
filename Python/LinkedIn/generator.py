# generator.py
import os
from openai import OpenAI, OpenAIError, RateLimitError
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_post_variants(title, summary, use_mock=True):
    if use_mock:
        return [
            f"[Fact] {title}: Key takeaways from the article.",
            f"[Analysis] Why it matters: {summary[:100]}...",
            f"[Story] Recently we discussed a similar topic — here's a quick overview.",
            f"[Expert] Here's my professional take on the topic: {title}",
            f"[Question] What do you think about this? Could it impact your work?",
            f"[Catchy] You won’t believe how this changes everything — {title}"
        ]

    prompt = f"""
    You are a professional LinkedIn content creator.

    Based on the following article:
    Title: {title}
    Summary: {summary}

    Generate 6 different LinkedIn posts **in English**, each with a distinct tone:
    1. Fact-based
    2. Analytical
    3. Storytelling / Engaging
    4. Expert opinion
    5. Provocative question
    6. Short and catchy

    Each post should be no longer than 500 characters and written in a professional but approachable tone.
    Do not include any titles or numbering in the output, just the posts themselves separated by blank lines.
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