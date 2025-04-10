# main.py
import streamlit as st
from parser import fetch_articles, load_config
from generator import generate_post_variants, generate_image_prompt, check_api_status
import os
import re
import yaml
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

st.title("AI LinkedIn Post Generator")

# 📅 Блок выбора даты
st.sidebar.markdown("### 📅 Фильтрация по дате")
default_date = datetime.now() - timedelta(days=7)
since_date = st.sidebar.date_input("Показать статьи с:", value=default_date.date())

# 🔘 Быстрые фильтры
preset = st.sidebar.radio("Быстрый выбор:", ["Последние 3 дня", "Последние 7 дней", "Последний месяц"], index=1)
if preset == "Последние 3 дня":
    since_date = datetime.now().date() - timedelta(days=3)
elif preset == "Последний месяц":
    since_date = datetime.now().date() - timedelta(days=30)

# ✅ Минимум совпадений ключевых слов
min_matches = st.sidebar.slider("Минимум совпадений ключевых слов:", min_value=1, max_value=5, value=1)

# 🔢 Лимит количества статей
article_limit = st.sidebar.slider("Максимум статей:", min_value=10, max_value=250, value=25, step=5)

# ⚙️ Технические опции
st.sidebar.markdown("---")
show_debug = st.sidebar.checkbox("🔍 Показать все статьи (режим отладки)")
use_soft_filter = st.sidebar.checkbox("🧠 Использовать мягкий фильтр (подстроки)")

articles, debug_log = fetch_articles(debug=show_debug, soft_filter=use_soft_filter, since_date=since_date, min_matches=min_matches, limit=article_limit)

if 'selected_articles' not in st.session_state:
    st.session_state.selected_articles = []

# Вкладки
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📰 Обзор статей", "⚙️ Генерация постов", "📋 Лог фильтрации", "🧩 Ключевые слова", "🔗 RSS-источники"])

with tab1:
    if not articles:
        st.warning("Нет подходящих статей. Проверьте источники или ключевые слова.")
    else:
        st.markdown("## 📚 Статьи для выбора:")
        for idx, article in enumerate(articles):
            with st.expander(article['title']):
                st.markdown(f"[Читать статью]({article['link']})")

                clean_summary = re.sub(r'<.*?>', '', article['summary'])
                st.caption(clean_summary[:300] + "...")

                if 'reason' in article:
                    st.caption(f"🧩 Совпадение по ключам: {article['reason']}")

                if st.checkbox("✅ Выбрать для генерации поста", key=f"select_{idx}"):
                    if idx not in st.session_state.selected_articles:
                        st.session_state.selected_articles.append(idx)
                else:
                    if idx in st.session_state.selected_articles:
                        st.session_state.selected_articles.remove(idx)

with tab2:
    if st.session_state.selected_articles:
        st.markdown("### ⚙️ Режим генерации GPT")
        use_mock = st.checkbox("🧪 Использовать офлайн-режим (мок-тест)", value=False)

        if not use_mock:
            st.info("💳 GPT работает в онлайн-режиме — будут использованы кредиты OpenAI API.")

        if st.button("🚀 Сгенерировать посты по выбранным статьям"):
            if not use_mock:
                api_status = check_api_status()
                if not api_status["ok"]:
                    st.error(f"❌ OpenAI GPT недоступен: {api_status['message']}")
                    st.stop()

            st.markdown("## ✍️ Сгенерированные посты")
            for idx in st.session_state.selected_articles:
                article = articles[idx]
                st.subheader(article['title'])
                st.markdown(f"[Читать статью]({article['link']})")

                posts = generate_post_variants(article['title'], article['summary'], use_mock=use_mock)
                styles = [
                    "📌 Фактологический",
                    "📊 Аналитический",
                    "📖 История / вовлекающий",
                    "🧠 Мнение / экспертный",
                    "💬 Провокационный вопрос",
                    "🪄 Коротко и цепко"
                ]

                for i, post in enumerate(posts):
                    style = styles[i] if i < len(styles) else f"💡 Вариант {i+1}"
                    st.markdown(f"### {style} пост", unsafe_allow_html=True)
                    st.markdown(post.strip(), unsafe_allow_html=True)
                    st.markdown("---")


                image_prompt = generate_image_prompt(article['summary'], use_mock=use_mock)
                st.text_input(
                    label=f"Промпт для графики (статья {idx+1})",
                    value=image_prompt,
                    key=f"gen_image_prompt_{idx}"
                )
    else:
        st.info("Выберите статьи на вкладке 'Обзор статей', чтобы активировать генерацию.")

with tab3:
    if show_debug and debug_log:
        st.markdown("### 🪵 Лог фильтрации:")
        for line in debug_log:
            st.text(line)
    else:
        st.info("Лог фильтрации доступен при включённом режиме отладки.")

with tab4:
    st.markdown("### 🧩 Ключевые слова для фильтрации статей")
    config_path = "config.yaml"
    config = load_config()
    keywords = config.get("keywords", [])

    st.markdown("#### ✅ Активные ключевые слова:")
    for word in keywords:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown(f"- {word}")
        with col2:
            if st.button("❌", key=f"del_kw_{word}"):
                keywords.remove(word)
                config["keywords"] = keywords
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(config, f, allow_unicode=True)
                st.success(f"Удалено: {word}")
                st.rerun()

    st.markdown("---")
    new_keyword = st.text_input("➕ Добавить новое ключевое слово")
    if st.button("Добавить ключ") and new_keyword:
        if new_keyword not in keywords:
            keywords.append(new_keyword)
            config["keywords"] = keywords
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, allow_unicode=True)
            st.success(f"Добавлено: {new_keyword}")
            st.rerun()
        else:
            st.warning("Такое ключевое слово уже есть.")

with tab5:
    st.markdown("### 🔗 RSS-источники")
    config_path = "config.yaml"
    config = load_config()
    rss_feeds = config.get("rss", [])

    st.markdown("#### 📡 Активные RSS-ссылки:")
    for url in rss_feeds:
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.markdown(f"- {url}")
        with col2:
            if st.button("❌", key=f"del_rss_{url}"):
                rss_feeds.remove(url)
                config["rss"] = rss_feeds
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(config, f, allow_unicode=True)
                st.success(f"Удалено: {url}")
                st.rerun()

    st.markdown("---")
    new_rss = st.text_input("➕ Добавить RSS-ссылку")
    if st.button("Добавить RSS") and new_rss:
        if new_rss not in rss_feeds:
            test_feed = feedparser.parse(new_rss)
            if test_feed.bozo:
                st.error("❌ Ошибка: ссылка недействительна или не является RSS.")
            else:
                rss_feeds.append(new_rss)
                config["rss"] = rss_feeds
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(config, f, allow_unicode=True)
                st.success(f"Добавлено: {new_rss}")
                st.rerun()
        else:
            st.warning("Такой RSS уже существует.")
