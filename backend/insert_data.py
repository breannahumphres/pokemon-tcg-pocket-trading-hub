import psycopg2
import json

DB_NAME = "pocket_tcg"
DB_USER = "postgres"
DB_PASSWORD = "brebre23"
DB_HOST = "localhost"
DB_PORT = "5432"

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password = DB_PASSWORD,
    host = DB_HOST,
    port = DB_PORT

)
cur = conn.cursor()

with open("pokemon_cards.json", "r", encoding = "utf-8") as file:
    cards = json.load(file)

for card in cards: 
    try:
        cur.execute("""
            INSERT INTO cards (name, type, set_name, rarity, image_url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (image_url) DO NOTHING;
        """, (card["name"], card["type"], card["set_name"], card["rarity"], card["image_url"]))
        print(f"Inserted: {card['name']}")
    except Exception as e:
        print(f"Error inserting {card['name']}: {e}")

conn.commit()
cur.close()
conn.close()

print("Data successfully inserted into the database")


