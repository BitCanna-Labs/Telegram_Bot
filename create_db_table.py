import sqlite3

# Conectar a la base de datos SQLite, se creará si no existe
conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

# Crear tabla
cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                  (chat_id INTEGER, address TEXT, balance INTEGER)''')
conn.commit()
conn.close()