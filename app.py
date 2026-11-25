import os
import streamlit as st
from dotenv import load_dotenv
from gigachat import GigaChat
from templates import TEMPLATES

load_dotenv()

st.set_page_config(page_title="QuizAI — Генератор викторин", page_icon="🎓", layout="centered")

st.title("🎓 QuizAI — Генератор учебных викторин")
st.write("Инструмент для учителей по созданию викторин по школьной программе на базе ИИ.")

with st.sidebar:
    st.header("⚙️ Настройки ИИ")
    env_key = os.getenv("GIGACHAT_CREDENTIALS", "")
    api_key = st.text_input(
        "API-ключ GigaChat:",
        value=env_key,
        type="password",
        help="Ключ автоматически подтягивается из файла .env, но его можно ввести и вручную."
    )
    st.info("💡 Все шаблоны адаптированы под ФГОС и школьную программу 5–11 классов.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    subject = st.selectbox(
        "Выберите предмет:",
        ["Информатика", "История", "Биология", "Физика", "Обществознание", "География", "Литература"]
    )
    grade = st.selectbox("Выберите класс:", list(range(5, 12)), index=5)

with col2:
    quiz_type = st.selectbox("Шаблон викторины:", list(TEMPLATES.keys()))
    num_questions = st.slider("Количество вопросов:", min_value=3, max_value=15, value=5)

topic = st.text_input("Введите тему урока:", placeholder="Например: Генетика и законы Менделя")
difficulty = st.radio("Сложность:", ["Лёгкая", "Средняя", "Сложная"], index=1, horizontal=True)

with st.expander("📄 Добавить свой текст / конспект урока (необязательно)"):
    source_text = st.text_area(
        "Вставьте текст параграфа или конспекта, чтобы вопросы строились строго по нему:",
        height=150,
        placeholder="Вставьте сюда текст..."
    )

if st.button("✨ Сгенерировать викторину", type="primary", use_container_width=True):
    if not api_key.strip():
        st.error("Введите API-ключ GigaChat в боковой панели слева или проверьте файл .env!")
    elif not topic.strip():
        st.warning("Пожалуйста, введите тему урока!")
    else:
        template_instruction = TEMPLATES[quiz_type]

        prompt = (
            f"Ты опытный школьный учитель и методист. Составь учебную викторину по предмету «{subject}» "
            f"для {grade} класса по теме «{topic}».\n"
            f"Количество вопросов: {num_questions}.\n"
            f"Уровень сложности: {difficulty}.\n"
            f"Формат и правила шаблона: {template_instruction}\n"
            f"Пиши грамотным, понятным для школьников языком без фактических ошибок."
        )

        if source_text.strip():
            prompt += f"\n\nОпирайся строго на следующий учебный текст:\n{source_text}"

        with st.spinner("🧠 GigaChat составляет вопросы по выбранному шаблону..."):
            try:
                with GigaChat(
                    credentials=api_key,
                    scope="GIGACHAT_API_PERS",
                    verify_ssl_certs=False
                ) as giga:
                    models_list = giga.get_models()
                    chosen_model = next(
                        (m.id_ for m in models_list.data if "GigaChat" in m.id_),
                        "GigaChat-2"
                    )

                    response = giga.chat({
                        "model": chosen_model,
                        "messages": [{"role": "user", "content": prompt}]
                    })
                    first_choice = next(iter(response.choices))
                    quiz_result = first_choice.message.content

                    st.session_state["quiz_result"] = quiz_result
                    st.session_state["quiz_title"] = f"{subject}_{grade}_класс_{topic}"
            except Exception as e:
                st.error(f"Ошибка при обращении к GigaChat: {e}")

if "quiz_result" in st.session_state:
    st.divider()
    st.subheader("📝 Готовая викторина")
    st.markdown(st.session_state["quiz_result"])

    st.download_button(
        label="📥 Скачать викторину в файл (.txt)",
        data=st.session_state["quiz_result"],file_name=f"{st.session_state['quiz_title']}.txt",
        mime="text/plain",
        use_container_width=True
    )