from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import mysql.connector
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'tracker123'  # Required for flash()

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456789",
    database="expense_tracker"
)

@app.route('/')
def index():
    category_filter = request.args.get('category', '').strip()
    date_filter = request.args.get('date', '').strip()

    query = "SELECT * FROM expenses"
    values = []
    filters = []

    if category_filter:
        filters.append("category = %s")
        values.append(category_filter)
    if date_filter:
        filters.append("date = %s")
        values.append(date_filter)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    with conn.cursor() as cursor:
        cursor.execute(query, tuple(values))
        expenses = cursor.fetchall()

        total = sum([row[4] for row in expenses])

        cursor.execute("SELECT DISTINCT category FROM expenses")
        categories = [row[0] for row in cursor.fetchall()]

    return render_template('index.html', expenses=expenses, total=total, categories=categories)

@app.route('/add', methods=['POST'])
def add_expense():
    date = request.form.get('date', '').strip() or datetime.today().strftime('%Y-%m-%d')
    category = request.form['category'].strip()
    description = request.form['description'].strip()
    amount = request.form['amount'].strip()

    try:
        amount = float(amount)
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO expenses (date, category, description, amount) VALUES (%s, %s, %s, %s)",
                (date, category, description, amount)
            )
        conn.commit()
        flash("✅ Expense added successfully!", "success")
    except ValueError as e:
        flash(f"❌ Invalid amount entered: {e}", "danger")

    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM expenses WHERE id = %s", (id,))
    conn.commit()
    flash("🗑️ Expense deleted.", "warning")
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update_expense(id):
    date = request.form['date'].strip()
    category = request.form['category'].strip()
    description = request.form['description'].strip()
    amount = request.form['amount'].strip()

    try:
        amount = float(amount)
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE expenses SET date=%s, category=%s, description=%s, amount=%s WHERE id=%s",
                (date, category, description, amount, id)
            )
        conn.commit()
        flash("✅ Expense updated.", "info")
    except ValueError as e:
        flash(f"❌ Invalid update: {e}", "danger")

    return redirect(url_for('index'))

@app.route('/export')
def export_csv():
    with conn.cursor() as cursor:
        cursor.execute("SELECT date, category, description, amount FROM expenses")
        data = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Description', 'Amount'])
    for row in data:
        writer.writerow(row)

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='expenses.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
