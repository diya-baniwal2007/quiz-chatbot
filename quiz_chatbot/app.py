import streamlit as st
import json
import random
import os
from datetime import datetime

st.set_page_config(page_title="AI Quiz Chatbot", page_icon="🤖", layout="wide")

# ------------------ Load Questions ------------------
def load_questions(topic, difficulty, tag_filter):
    filepath = f"data/{topic}_questions.json"

    try:
        with open(filepath, "r") as f:
            questions = json.load(f)
    except FileNotFoundError:
        st.error(f"🚫 File not found: `{filepath}`")
        return []
    except Exception as e:
        st.error(f"❌ Error loading `{filepath}`: {e}")
        return []

    st.write(f"✅ Loaded file: `{filepath}`")
    st.write(f"📦 Total questions in file: {len(questions)}")

    filtered = [
        q for q in questions
        if q.get("difficulty") == difficulty and (tag_filter == "All" or q.get("tag") == tag_filter)
    ]

    st.write(f"🔍 Questions after filtering: {len(filtered)}")
    return filtered

# ------------------ Save Score ------------------
def save_score(name, score, total, topic):
    data_file = "leaderboard.json"
    entry = {
        "name": name,
        "score": score,
        "total": total,
        "topic": topic,
        "timestamp": str(datetime.now())
    }
    if os.path.exists(data_file):
        try:
            with open(data_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []
    data.append(entry)
    with open(data_file, "w") as f:
        json.dump(data, f)

# ------------------ Show Leaderboard ------------------
def show_leaderboard():
    if not os.path.exists("leaderboard.json"):
        st.info("No leaderboard data available yet.")
        return

    with open("leaderboard.json", "r") as f:
        data = json.load(f)

    sorted_data = sorted(data, key=lambda x: x["score"], reverse=True)
    st.subheader("🏆 Leaderboard Result")
    for i, entry in enumerate(sorted_data[:10]):
        st.markdown(f"{i+1}. **{entry['name']}** - {entry['score']}/{entry['total']} ({entry.get('topic', 'N/A')})")

# ------------------ App Start ------------------
st.markdown("## 🤖 AI Quiz Chatbot")

# Sidebar Setup
st.sidebar.header("🧠 Quiz Setup")
name = st.sidebar.text_input("Enter your name:", "")
topic = st.sidebar.selectbox("Choose Topic", ["math", "science", "general"])
difficulty = st.sidebar.selectbox("Select Difficulty", ["easy", "medium", "hard"])
num_questions = st.sidebar.selectbox("Questions to attempt", [10, 20, 50])
time_per_question = st.sidebar.slider("Time per question (seconds):", 10, 60, 30)
tag_filter = st.sidebar.selectbox("Filter by Tag", ["All", "algebra", "geometry", "biology", "history"])

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if st.sidebar.button("Start Quiz"):
    st.session_state.quiz_started = True
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.questions = load_questions(topic, difficulty, tag_filter)
    st.session_state.selected = []
    if len(st.session_state.questions) < num_questions:
        st.warning(f"Only {len(st.session_state.questions)} questions available. Adjusting quiz size.")
        num_questions = len(st.session_state.questions)
    random.shuffle(st.session_state.questions)
    st.session_state.questions = st.session_state.questions[:num_questions]
    st.session_state.total = len(st.session_state.questions)

if st.session_state.quiz_started:
    if st.session_state.current_q < st.session_state.total:
        q = st.session_state.questions[st.session_state.current_q]
        st.markdown(f"### Question {st.session_state.current_q + 1}: {q['question']}")
        options = q['options']
        answer = st.radio("Choose an option:", options, key=f"q{st.session_state.current_q}")
        if st.button("Next Question"):
            if answer == q['answer']:
                st.session_state.score += 1
            st.session_state.current_q += 1
            st.rerun()
    else:
        st.markdown("## 🎉 Quiz Completed!")
        st.success(f"**{name}**, your final score is {st.session_state.score}/{st.session_state.total}")

        # Show feedback
        if st.session_state.total == 0:
            st.warning("⚠️ No questions attempted.")
        elif st.session_state.score == st.session_state.total:
            st.success("🌟 Incredible! You got a **perfect score**!")
            st.markdown("Your basics are **rock solid**. Keep up the amazing work! 💪🧠")
        elif st.session_state.score >= st.session_state.total * 0.7:
            st.info("👍 Good job! But you can improve further.")
        else:
            st.error("📚 You need to work on key topics. Keep practicing!")

        # Save and show leaderboard
        save_score(name, st.session_state.score, st.session_state.total, topic)
        show_leaderboard()

        if st.button("Restart Quiz"):
            st.session_state.quiz_started = False
            st.rerun()
