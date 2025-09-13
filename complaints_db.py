import sqlite3
import os
import csv
from textblob import TextBlob
from datetime import datetime

DB_NAME = "complaints.db"


def init_db():
    """Initialize SQLite database and create tables if not exist."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Customers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT
    )
    """)

    # Complaints table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        category TEXT,
        description TEXT,
        status TEXT DEFAULT 'Open',
        created_at TEXT,
        sentiment TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """)

    # Interactions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        complaint_id INTEGER,
        message TEXT,
        sender TEXT,
        sentiment TEXT,
        timestamp TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(complaint_id) REFERENCES complaints(id)
    )
    """)

    # Metrics table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        total_complaints INTEGER DEFAULT 0,
        resolved_complaints INTEGER DEFAULT 0,
        escalations INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def get_or_create_customer(name, contact):
    """Fetch existing customer or create a new one."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM customers WHERE lower(name)=lower(?) AND contact=?", (name, contact))
    row = cur.fetchone()

    if row:
        customer_id = row[0]
    else:
        cur.execute("INSERT INTO customers (name, contact) VALUES (?, ?)", (name, contact))
        conn.commit()
        customer_id = cur.lastrowid

    conn.close()
    return customer_id


def analyze_sentiment(text):
    """Run sentiment analysis on complaint or message text."""
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"


def update_metrics(field):
    """Increment a metrics counter by field for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT id FROM metrics WHERE date=?", (today,))
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO metrics (date, total_complaints, resolved_complaints, escalations) VALUES (?, 0, 0, 0)", (today,))
        conn.commit()

    cur.execute(f"UPDATE metrics SET {field} = {field} + 1 WHERE date=?", (today,))
    conn.commit()
    conn.close()


def book_complaint(customer_name, contact, category, description):
    """Register a new complaint with sentiment and update metrics."""
    customer_id = get_or_create_customer(customer_name, contact)
    sentiment = analyze_sentiment(description)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO complaints (customer_id, category, description, created_at, sentiment)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, category, description, created_at, sentiment))
    conn.commit()
    complaint_id = cur.lastrowid
    conn.close()

    update_metrics("total_complaints")

    return {
        "complaint_id": complaint_id,
        "message": f"Complaint {complaint_id} registered for {customer_name} in category '{category}'.",
        "status": "Open",
        "sentiment": sentiment
    }


def check_status(complaint_id):
    """Check complaint status by ID."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, cu.name, cu.contact, c.category, c.description, c.status, c.created_at, c.sentiment
        FROM complaints c
        JOIN customers cu ON c.customer_id = cu.id
        WHERE c.id = ?
    """, (complaint_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "complaint_id": row[0],
            "customer": row[1],
            "contact": row[2],
            "category": row[3],
            "description": row[4],
            "status": row[5],
            "created_at": row[6],
            "sentiment": row[7]
        }
    return {"error": f"Complaint {complaint_id} not found"}


def get_customer_history(customer_name):
    """Retrieve all complaints for a customer by name."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.category, c.description, c.status, c.created_at, c.sentiment
        FROM complaints c
        JOIN customers cu ON c.customer_id = cu.id
        WHERE lower(cu.name) = lower(?)
    """, (customer_name,))
    rows = cur.fetchall()
    conn.close()

    if rows:
        history = [
            {
                "id": r[0],
                "category": r[1],
                "description": r[2],
                "status": r[3],
                "created_at": r[4],
                "sentiment": r[5]
            }
            for r in rows
        ]
        return {"customer": customer_name, "history": history}
    return {"error": f"No complaints found for {customer_name}"}


def escalate_complaint(complaint_id, reason):
    """Escalate a complaint with a reason and update metrics."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM complaints WHERE id=?", (complaint_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": f"Complaint {complaint_id} not found"}

    cur.execute("UPDATE complaints SET status='Escalated' WHERE id=?", (complaint_id,))
    conn.commit()
    conn.close()

    update_metrics("escalations")

    return {
        "complaint_id": complaint_id,
        "status": "Escalated",
        "reason": reason,
        "message": f"Complaint {complaint_id} has been escalated due to: {reason}"
    }


def resolve_complaint(complaint_id):
    """Mark complaint as resolved and update metrics."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM complaints WHERE id=?", (complaint_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": f"Complaint {complaint_id} not found"}

    cur.execute("UPDATE complaints SET status='Resolved' WHERE id=?", (complaint_id,))
    conn.commit()
    conn.close()

    update_metrics("resolved_complaints")

    return {
        "complaint_id": complaint_id,
        "status": "Resolved",
        "message": f"Complaint {complaint_id} has been marked as resolved."
    }


def export_report(customer_name):
    """Export complaints of a customer to a CSV file and return JSON."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.category, c.description, c.status, c.created_at, c.sentiment
        FROM complaints c
        JOIN customers cu ON c.customer_id = cu.id
        WHERE lower(cu.name) = lower(?)
    """, (customer_name,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"error": f"No complaints found for {customer_name}"}

    os.makedirs("reports", exist_ok=True)
    filename = f"{customer_name.replace(' ', '_').lower()}_report.csv"
    filepath = os.path.join("reports", filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Complaint ID", "Category", "Description", "Status", "Created At", "Sentiment"])
        writer.writerows(rows)

    complaints = [
        {"id": r[0], "category": r[1], "description": r[2], "status": r[3], "created_at": r[4], "sentiment": r[5]}
        for r in rows
    ]

    return {
        "customer": customer_name,
        "exported_complaints": complaints,
        "csv_file": filepath,
        "message": f"Report exported successfully to {filepath}"
    }


def get_complaints_by_sentiment(sentiment):
    """Retrieve complaints filtered by sentiment."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, cu.name, cu.contact, c.category, c.description, c.status, c.created_at, c.sentiment
        FROM complaints c
        JOIN customers cu ON c.customer_id = cu.id
        WHERE lower(c.sentiment) = lower(?)
    """, (sentiment,))
    rows = cur.fetchall()
    conn.close()

    if rows:
        return [
            {
                "id": r[0],
                "customer": r[1],
                "contact": r[2],
                "category": r[3],
                "description": r[4],
                "status": r[5],
                "created_at": r[6],
                "sentiment": r[7]
            }
            for r in rows
        ]
    return {"error": f"No complaints found with sentiment '{sentiment}'"}


def log_interaction(customer_id, complaint_id, message, sender="user"):
    """Log a customer-agent interaction with sentiment."""
    sentiment = analyze_sentiment(message)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO interactions (customer_id, complaint_id, message, sender, sentiment, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_id, complaint_id, message, sender, sentiment, timestamp))
    conn.commit()
    conn.close()


# Function mapping dictionary
FUNCTION_MAP = {
    'book_complaint': book_complaint,
    'check_status': check_status,
    'get_customer_history': get_customer_history,
    'escalate_complaint': escalate_complaint,
    'resolve_complaint': resolve_complaint,
    'export_report': export_report,
    'analyze_sentiment': analyze_sentiment,
    'get_complaints_by_sentiment': get_complaints_by_sentiment,
    'log_interaction': log_interaction
}


if __name__ == "__main__":
    init_db()
    print("✅ Database initialized and ready.")
