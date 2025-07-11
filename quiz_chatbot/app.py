import streamlit as st
import json
import random
import os
import time

st.set_page_config(page_title="AI Quiz Chatbot", page_icon="🤖", layout="wide")

# Function to load quiz questions
def load_questions(topic, difficulty):
    file_path = f"data/{topic}_{difficulty}.json"
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ File not found: {file_path}")
        return []

# Function to save score to leaderboard
def save_score(name, score, total, topic):
    leaderboard_file = "leaderboard.json"
    if os.path.exists(leaderboard_file):
        with open(leaderboard_file, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append({"name": name, "score": score, "total": total, "topic": topic})
    with open(leaderboard_file, "w") as f:
        json.dump(data, f)

# Function to display leaderboard
def show_leaderboard(name, score, total, topic):
    st.subheader("🏆 Leaderboard Result")
    leaderboard_file = "leaderboard.json"
    try:
        with open(leaderboard_file, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append({"name": name, "score": score, "total": total, "topic": topic})
    sorted_data = sorted(data, key=lambda x: x['score'], reverse=True)

    rank = next((i+1 for i, entry in enumerate(sorted_data) if entry['name'] == name and entry['score'] == score), None)

    st.success(f"You ranked #{rank} out of {len(sorted_data)} participants!")

# Function to generate feedback based on score
def generate_feedback(score, total):
    if total == 0:
        return "⚠️ No questions attempted."
    percentage = (score / total) * 100
    if percentage == 100:
        return "🌟 Incredible! You got a **perfect score**!\n\nYour basics are **rock solid**. Keep up the amazing work! 💪🧠"
    elif percentage >= 70:
        return "🎯 Great job! You did really well.\n\nKeep practicing to become a master! 💡"
    elif percentage >= 40:
        return "🧐 Not bad! But you need to work on a few areas.\n\nReview the topics where you made mistakes and try again!"
    else:
        return "📚 You need to practice more.\n\nFocus on understanding the fundamentals first. You got this! 💪"

# -------------------- Streamlit UI --------------------

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "score" not in st.session_state:
    st.session_state.score = 0
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "selected_answers" not in st.session_state:
    st.session_state.selected_answers = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None

with st.sidebar:
    st.markdown("## 🧠 Quiz Setup")
    name = st.text_input("Enter your name:", key="name")
    topic = st.selectbox("Choose Topic", ["math", "science", "general"])
    difficulty = st.selectbox("Select Difficulty", ["easy", "medium", "hard"])
    num_questions = st.selectbox("Questions to attempt", [10, 20, 50])
    time_per_question = st.slider("Time per question (seconds):", 10, 60, 30)
    tag_filter = st.selectbox("Filter by Tag", ["All", "algebra", "geometry", "physics", "chemistry", "history", "biology"])

    if st.button("Start Quiz"):
        questions = load_questions(topic, difficulty)
        if tag_filter != "All":
            questions = [q for q in questions if tag_filter.lower() in q.get("tag", "").lower()]
        if not questions:
            st.warning("No questions found for this filter. Please try another.")
        else:
            random.shuffle(questions)
            st.session_state.quiz_data = questions[:num_questions]
            st.session_state.quiz_started = True
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.selected_answers = []
            st.session_state.start_time = time.time()

# -------------------- Quiz Display --------------------

if st.session_state.quiz_started:
    current_index = st.session_state.current_q
    questions = st.session_state.quiz_data

    if current_index < len(questions):
        q = questions[current_index]
        time_left = time_per_question - int(time.time() - st.session_state.start_time)

        st.markdown(f"### 🤖 AI Quiz Chatbot")
        st.markdown(f"**Question {current_index+1}:** {q['question']}")
        st.info(f"⏳ Time remaining: {time_left}s")

        if time_left <= 0:
            st.warning("⏰ Time's up! Moving to next question...")
            st.session_state.selected_answers.append("Timeout")
            st.session_state.current_q += 1
            st.session_state.start_time = time.time()
            st.experimental_rerun()

        options = q.get("options", [])
        selected = st.radio("Select your answer:", options, key=f"q_{current_index}")
        if st.button("Next Question"):
            correct = q.get("answer")
            if selected == correct:
                st.session_state.score += 1
            st.session_state.selected_answers.append(selected)
            st.session_state.current_q += 1
            st.session_state.start_time = time.time()
            st.experimental_rerun()
    else:
        # Quiz Completed
        st.session_state.quiz_started = False
        score = st.session_state.score
        total = len(questions)
        st.markdown("## 🎉 Quiz Completed!")
        st.success(f"{name}, your final score is {score}/{total}")
        st.info(generate_feedback(score, total))
        save_score(name, score, total, topic)
        show_leaderboard(name, score, total, topic)
        st.button("Restart Quiz", on_click=lambda: st.experimental_rerun())
