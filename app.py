import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from textblob import TextBlob
import matplotlib.pyplot as plt
import plotly.express as px
from reportlab.pdfgen import canvas
import os
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download required NLTK data
nltk.download('vader_lexicon')

# Initialize database
def init_db():
    conn = sqlite3.connect('mindmirror.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  content TEXT,
                  sentiment REAL,
                  mood TEXT)''')
    conn.commit()
    conn.close()

# Add journal entry
def add_entry(content):
    # Analyze sentiment
    sia = SentimentIntensityAnalyzer()
    sentiment_score = sia.polarity_scores(content)['compound']
    
    # Determine mood based on sentiment score
    if sentiment_score >= 0.5:
        mood = "Happy"
    elif sentiment_score >= 0:
        mood = "Neutral"
    else:
        mood = "Sad"
    
    conn = sqlite3.connect('mindmirror.db')
    c = conn.cursor()
    c.execute("INSERT INTO entries (date, content, sentiment, mood) VALUES (?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), content, sentiment_score, mood))
    conn.commit()
    conn.close()

# Get all entries
def get_entries():
    conn = sqlite3.connect('mindmirror.db')
    df = pd.read_sql_query("SELECT * FROM entries ORDER BY date DESC", conn)
    conn.close()
    return df

# Generate affirmation based on mood
def generate_affirmation(mood):
    affirmations = {
        "Happy": "Your positive energy is contagious! Keep spreading joy.",
        "Neutral": "Every moment is a new opportunity for growth.",
        "Sad": "Remember, this too shall pass. You are stronger than you think."
    }
    return affirmations.get(mood, "Take a deep breath and be present in this moment.")

# Export entries to PDF
def export_to_pdf():
    entries = get_entries()
    filename = f"mindmirror_export_{datetime.now().strftime('%Y%m%d')}.pdf"
    c = canvas.Canvas(filename)
    
    y = 750
    for _, entry in entries.iterrows():
        c.drawString(50, y, f"Date: {entry['date']}")
        c.drawString(50, y-20, f"Mood: {entry['mood']}")
        c.drawString(50, y-40, f"Content: {entry['content'][:100]}...")
        y -= 60
        if y < 50:
            c.showPage()
            y = 750
    
    c.save()
    return filename

# Main Streamlit app
def main():
    st.title("MindMirror - Your Personal Journal")
    
    # Initialize database
    init_db()
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Journal Entry", "Mood History", "Export"])
    
    if page == "Journal Entry":
        st.header("Write Your Thoughts")
        content = st.text_area("How are you feeling today?", height=200)
        
        if st.button("Save Entry"):
            if content:
                add_entry(content)
                st.success("Entry saved successfully!")
                # Show affirmation
                mood = TextBlob(content).sentiment.polarity
                affirmation = generate_affirmation("Happy" if mood > 0 else "Sad" if mood < 0 else "Neutral")
                st.info(f"Daily Affirmation: {affirmation}")
            else:
                st.warning("Please write something before saving.")
    
    elif page == "Mood History":
        st.header("Your Mood History")
        entries = get_entries()
        
        if not entries.empty:
            # Plot mood over time
            fig = px.line(entries, x='date', y='sentiment', 
                         title='Mood Over Time',
                         labels={'sentiment': 'Sentiment Score', 'date': 'Date'})
            st.plotly_chart(fig)
            
            # Show recent entries
            st.subheader("Recent Entries")
            for _, entry in entries.head(5).iterrows():
                st.write(f"**{entry['date']}** - {entry['mood']}")
                st.write(entry['content'])
                st.write("---")
        else:
            st.info("No entries yet. Start journaling!")
    
    elif page == "Export":
        st.header("Export Your Journal")
        if st.button("Export to PDF"):
            filename = export_to_pdf()
            st.success(f"Journal exported to {filename}")
            st.info("You can find the PDF in your current directory.")

if __name__ == "__main__":
    main() 