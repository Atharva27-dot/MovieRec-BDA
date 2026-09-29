# Step-by-Step Demonstration Flow for Professor Presentation

Follow these 13 steps when presenting `MovieRec-BDA` to your professor or lab evaluator:

---

### Step 1: Launch Application
Open terminal and run:
```powershell
streamlit run app.py
```
Show that the application opens smoothly in the web browser at `http://localhost:8501`.

---

### Step 2: Show Home Page & KPI Cards
- Highlight the 4 KPI metric cards: **Total Movies**, **Total Ratings**, **Average Rating**, and **Total Genres**.
- Show the architecture diagram and data source status indicator.

---

### Step 3: Show MongoDB Connection Status
- Point to the sidebar indicator: **🟢 Connected to MongoDB Atlas** (or local mode status).
- Explain that connection credentials are stored securely in `.env`.

---

### Step 4: Open Movie Explorer
- Navigate to **"2. Movie Explorer"**.
- Demonstrate searching for a movie title (e.g., *"Toy Story"* or *"Dark Knight"*).
- Filter by genre (e.g., *"Action"* or *"Animation"*).
- Select a movie to view detailed statistics (Movie ID, Average Rating, Rating Count, Genres).

---

### Step 5: Open Recommendation Engine
- Navigate to **"3. Recommendations"**.
- Select a target movie (e.g., *"Toy Story (1995)"*).
- Select Top 10 recommendations and click **"🚀 Get Recommendations"**.

---

### Step 6: Explain Similarity & Hybrid Score
- Point out the top recommended movie (e.g., *"A Bug's Life (1998)"*).
- Show the **Similarity Score** (1.00) and **Matching Genres** (*Adventure, Animation, Children, Comedy*).
- Explain the explanation text: *"Shares 4 genre(s)..."*.

---

### Step 7: Open Analytics Dashboard
- Navigate to **"4. Analytics Dashboard"**.
- Show Tab 1: **Rating Value Frequency Distribution** (bar chart of 0.5 to 5.0 stars).

---

### Step 8: Show Top Rated Movies Chart
- Show Tab 2: **Top 10 Most Rated Movies** vs **Top 10 Highest Rated Movies**.
- Adjust the **Minimum Rating Count Threshold Slider** to show dynamic chart updates.

---

### Step 9: Show Genre Distribution
- Show Tab 3: **Movie Distribution by Genre** pie chart.

---

### Step 10: Open MongoDB Operations Page
- Navigate to **"5. MongoDB Operations"**.
- Explain that MongoDB is performing analytics on the database server.

---

### Step 11: Execute Interactive MongoDB Aggregations
- Select query option **"4. db.ratings.aggregate([$group, $sort, $limit])"**.
- Show the live MongoDB code and returned JSON document results.

---

### Step 12: Explain "Why MongoDB?"
- Read the 4 bullet points explaining Document-oriented storage, Aggregation Framework, Indexing, and Schema flexibility.

---

### Step 13: Open About Project Page & Conclude
- Navigate to **"6. About Project"**.
- Summarize Problem Statement, BDA Concepts, Objectives, and Team Members.
