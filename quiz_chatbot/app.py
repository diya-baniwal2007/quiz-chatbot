import streamlit as st
import json
import os
import time
from fuzzywuzzy import fuzz

st.set_page_config(page_title="Quiz Chatbot", page_icon="🧠")

# Sidebar for quiz setup
st.sidebar.title("🧠 Quiz Setup")
name = st.sidebar.text_input("Enter your name:")
topic = st.sidebar.selectbox("Choose Topic", ["math", "general", "science"])
difficulty = st.sidebar.selectbox("Select Difficulty", ["easy", "medium", "hard"])
question_count = st.sidebar.selectbox("Questions to attempt", [10, 20, 50])
time_limit = st.sidebar.slider("Time per question (seconds):", 10, 60, 30)

# Tag filter setup
tag_options = ["All"]
tag_file = f"data/{topic}_{difficulty}.json"
if os.path.exists(tag_file):
    with open(tag_file, "r") as f:
        tags = list(set([q.get("tag", "") for q in json.load(f)]))
        tag_options += sorted([t for t in tags if t])
tag_filter = st.sidebar.selectbox("Filter by Tag", tag_options)

# Function to load questions
def load_questions(topic, difficulty, tag):
    path = f"data/{topic}_{difficulty}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            if tag != "All":
                data = [q for q in data if q.get("tag") == tag]
            return data
    return []

# Function to save user score
def save_score(name, score, total, topic):
    entry = {"name": name, "score": score, "total": total, "topic": topic}
    if not os.path.exists("scores.json"):
        with open("scores.json", "w") as f:
            json.dump([entry], f, indent=2)
    else:
        with open("scores.json", "r") as f:
            data = json.load(f)
        data.append(entry)
        with open("scores.json", "w") as f:
            json.dump(data, f, indent=2)

# Main title
st.title("🤖 AI Quiz Chatbot")

# Start quiz setup
if name and st.sidebar.button("Start Quiz"):
    st.session_state.started = True
    st.session_state.name = name
    st.session_state.topic = topic
    st.session_state.difficulty = difficulty
    st.session_state.tag = tag_filter
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.time_limit = time_limit
    st.session_state.question_start = time.time()
    st.session_state.questions = load_questions(topic, difficulty, tag_filter)[:question_count]
    st.rerun()

# Quiz logic
if st.session_state.get("started"):
    questions = st.session_state.questions
    q_index = st.session_state.q_index

    if q_index < len(questions):
        current = questions[q_index]
        st.markdown(f"**Question {q_index + 1}:** {current['question']}")
        elapsed = time.time() - st.session_state.question_start
        remaining = max(0, st.session_state.time_limit - int(elapsed))
        st.info(f"⏱️ Time remaining: {remaining}s")

        options = current.get("options")
        answer = None

        if "answered" not in st.session_state:
            if remaining <= 0:
                st.warning("⏰ Time's up!")
                st.session_state.answered = "[TIMEOUT]"
                st.session_state.history.append({
                    "question": current["question"],
                    "user_answer": "[TIMEOUT]",
                    "correct": False,
                    "tag": current.get("tag", "")
                })
            else:
                if options:
                    answer = st.radio("Choose an option:", options, key=f"radio_{q_index}")
                else:
                    answer = st.text_input("Type your answer:", key=f"text_{q_index}")

                if st.button("Submit", key=f"submit_{q_index}"):
                    correct_answer = current["answer"]
                    if options:
                        is_correct = answer == correct_answer
                    else:
                        is_correct = fuzz.ratio(answer.lower(), correct_answer.lower()) > 80

                    st.session_state.answered = answer
                    if is_correct:
                        st.success(f"✅ Correct answer!")
                        st.session_state.score += 1
                    else:
                        st.error(f"❌ Incorrect answer.")
                        st.info(f"Correct Answer: {correct_answer}")

                    st.info(f"📘 Explanation: {current.get('explanation', 'No explanation provided.')}")
                    st.session_state.history.append({
                        "question": current["question"],
                        "user_answer": answer,
                        "correct": is_correct,
                        "tag": current.get("tag", "")
                    })

        else:
            if st.button("Next Question"):
                st.session_state.q_index += 1
                del st.session_state["answered"]
                st.session_state.question_start = time.time()
                st.rerun()

    else:
        # Quiz finished
        st.header("🎉 Quiz Completed!")
        score = st.session_state.score
        total = len(questions)
        st.success(f"{st.session_state.name}, your final score is **{score}/{total}**.")
        save_score(name, score, total, topic)

        # Personalized Feedback
        wrong = [q for q in st.session_state.history if not q['correct']]
        if score == total:
            st.balloons()
            st.success("🌟 Incredible! You got a **perfect score**!")
            st.markdown("Your basics are **rock solid**. Keep up the amazing work! 💪🧠")
        elif wrong:
            st.subheader("📊 Personalized Feedback")
            weak_tags = {}
            for q in wrong:
                tag = q.get("tag", "Untagged")
                weak_tags[tag] = weak_tags.get(tag, 0) + 1
            weakest = sorted(weak_tags.items(), key=lambda x: x[1], reverse=True)

            st.warning("You need to work on the following areas:")
            for tag, count in weakest:
                st.markdown(f"- **{tag}**: {count} incorrect")

            st.info("🔁 Practice those topics again. You're improving!")

        # Show leaderboard
        if os.path.exists("scores.json"):
            with open("scores.json", "r") as f:
                data = json.load(f)
            data_sorted = sorted(data, key=lambda x: x['score'], reverse=True)
            rank = [x['name'] for x in data_sorted]
            user_rank = rank.index(name) + 1
            total_players = len(rank)
            st.subheader("🏆 Leaderboard Result")
            st.success(f"You ranked **#{user_rank}** out of **{total_players}** participants!")

        if st.button("Restart Quiz"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
