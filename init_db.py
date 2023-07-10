import sqlite3

connection = sqlite3.connect('instance/todos.db')  # file path

# create a cursor object from the cursor class
cur = connection.cursor()

cur.execute('''
   CREATE TABLE User(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       email TEXT NOT NULL, 
       password TEXT NOT NULL,    
       token TEXT NULL,    
       token_expiration_date TEXT NOT NULL    
   )''')

cur.execute('''
   CREATE TABLE Todo(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       user_id INTEGER NOT NULL, 
       todo TEXT NOT NULL,
       due TEXT NULL    
   )''')

print("\nDatabase created successfully!!!")
# committing our connection
connection.commit()

# close our connection
connection.close()
