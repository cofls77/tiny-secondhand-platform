import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

############################
# USERS
############################

cur.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    nickname TEXT,

    point INTEGER DEFAULT 10000,

    role TEXT DEFAULT 'user',

    is_dormant INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

############################
# PRODUCTS
############################

cur.execute("""
CREATE TABLE IF NOT EXISTS products(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    description TEXT NOT NULL,

    price INTEGER NOT NULL,

    seller_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(seller_id) REFERENCES users(id)

)
""")

############################
# CHAT ROOM
############################

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_rooms(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_id INTEGER NOT NULL,

    buyer_id INTEGER NOT NULL,

    seller_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(product_id) REFERENCES products(id),

    FOREIGN KEY(buyer_id) REFERENCES users(id),

    FOREIGN KEY(seller_id) REFERENCES users(id)

)
""")

############################
# MESSAGES
############################

cur.execute("""
CREATE TABLE IF NOT EXISTS messages(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    room_id INTEGER NOT NULL,

    sender_id INTEGER NOT NULL,

    message TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(room_id) REFERENCES chat_rooms(id),

    FOREIGN KEY(sender_id) REFERENCES users(id)

)
""")

############################
# TRANSFERS
############################

cur.execute("""
CREATE TABLE IF NOT EXISTS transfers(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sender_id INTEGER NOT NULL,

    receiver_id INTEGER NOT NULL,

    amount INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(sender_id) REFERENCES users(id),

    FOREIGN KEY(receiver_id) REFERENCES users(id)

)
""")
############################
# REPORTS
############################

cur.execute("""
CREATE TABLE IF NOT EXISTS reports(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    reporter_id INTEGER NOT NULL,

    target_user_id INTEGER,

    product_id INTEGER,

    reason TEXT NOT NULL,

    status TEXT DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    FOREIGN KEY(reporter_id)
    REFERENCES users(id),


    FOREIGN KEY(target_user_id)
    REFERENCES users(id),


    FOREIGN KEY(product_id)
    REFERENCES products(id)

)
""")
conn.commit()
conn.close()

print("DB Created")