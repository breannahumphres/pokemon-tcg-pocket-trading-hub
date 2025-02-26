from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname="pocket_tcg",
        user="postgres",
        password="brebre23",
        host="localhost",
        port="5432"
    )

#Home Route
@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Pokemon Pocket TCG Trading Hub API!"})

#Get All Cards
@app.route('/cards',methods=['GET'])
def get_cards():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM cards;")
    cards = cursor.fetchall()
    conn.close()
    return jsonify(cards)

#Get Specific Card by ID
@app.route('/cards/<int:card_id>',methods=['GET'])
def get_card(card_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM cards WHERE id = %s;", (card_id,))
    card = cursor.fetchone()
    conn.close()
    if card:
        return jsonify(card)
    return jsonify({"error": "Card not found"}), 404

#Get All Users
@app.route('/users',methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users;")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

#Get Specific User by ID
@app.route('/users/<int:user_id>',methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

#Add a New User
@app.route("/users", methods=["POST"])
def add_user():
    data = request.json
    required_fields = ["username", "email", "password", "pokemon_tcg_username"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    hashed_password = generate_password_hash(data["password"], method = 'pbkdf2:sha256', salt_length=8)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, bio, profile_picture, pokemon_tcg_username, links) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *;",
        (
            data["username"], 
            data["email"], 
            hashed_password,
            data.get("bio", ""), 
            data.get("profile_picture", ""),
            data.get("pokemon_tcg_username", ""),
            data.get("links", "")),
    )
    new_user = cursor.fetchone()
    conn.commit()
    conn.close()
    return jsonify(new_user), 201

#update a user profile
@app.route("/users/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user: 
        conn.close()
        return jsonify({"error": "user not found"}), 404

    cursor.execute("UPDATE users SET username = COALESCE(%s, username) WHERE id = %s",
                   (data.get("username"), user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "user updated successfully"})

#update password
@app.route("/users/<int:user_id>/password", methods=["PATCH"])
def update_password(user_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor() 
    cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({"error":"User not found"}), 404
  
    if "current_password" not in data or "new_password" not in data:
        conn.close()
        return jsonify({"error": "both current_password and new_password are required"}), 400
    if not check_password_hash(user[0], data["current_password"]):
        conn.close()
        return jsonify({"error": "current password is incorrect"}), 401
    if len(data["new_password"]) < 8:
        conn.close()
        return jsonify({"error":"new password must be at least 8 characters long"}), 400
    
    hashed_password = generate_password_hash(data["new_password"], method = "pbkdf2:sha256", salt_length=8)
    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_password, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Password updated successfully"})


#Add a card to a user's collection
@app.route("/user_cards", methods=["POST"])
def add_user_card():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_cards (user_id, card_id, quantity) VALUES (%s, %s, %s) RETURNING *;",
        (data["user_id"], data["card_id"], data.get("quantity", 1))
    )
    new_entry = cursor.fetchone()
    conn.commit()
    conn.close()
    return jsonify(new_entry), 201

#update card quantity
@app.route("/cards/<int:user_id>/<int:card_id>", methods=["PATCH"])
def update_card_quantity(user_id, card_id):
    data = request.json
    new_quantity = data.get("quantity")
    if new_quantity is None or new_quantity <0:
        return jsonify({"error": 'invalid quantity'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_cards WHERE user_id = %s AND card_id = %s", (user_id, card_id))
    user_card = cursor.fetchone()
    if not user_card:
        conn.close()
        return jsonify({"error": "card not found in user collection"})
    
    cursor.execute("UPDATE user_cards SET quantity = %s WHERE user_id = %s AND card_id = %s", (data["quantity"], user_id, card_id))

    conn.commit()
    conn.close()
    return jsonify({"message": "Card quantity updated"}), 200

#Add a Card to Wishlist
@app.route("/wishlist", methods=["POST"])
def add_wishlist():
    data = request.json
    user_id = data["user_id"]
    card_id = data["card_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wishlist WHERE user_id = %s AND card_id = %s", (user_id, card_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Card already in wishlist"}), 400

    cursor.execute(
        "SELECT COUNT(*) FROM wishlist WHERE user_id = %s;", (user_id,))
    wishlist_count = cursor.fetchone()[0]
    
    if wishlist_count >= 3:
        conn.close()
        return jsonify({"error": "You can only have 3 items in your wishlist"}), 400
    
    cursor.execute(
        "INSERT INTO wishlist (user_id, card_id) VALUES (%s, %s) RETURNING *;",
        (user_id, card_id)
    )
    new_entry = cursor.fetchone()
    conn.commit()
    conn.close()
    return jsonify(new_entry), 201

#update a users wishlist
@app.route("/wishlist/<int:item_id>", methods=["PATCH"])
def update_wishlist(item_id):
    data=request.get_json()
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("UPDATE wishlist SET card_id = COALESCE(%s, card_id), priority = COALESCE(%s, priority), notes = COALESCE(%s, notes) WHERE id = %s", (data.get("card_id"), data.get("priority"), data.get("notes"), item_id))

    conn.commit()
    conn.close()
    return jsonify({"message":"Wishlist item updated!"})

#Get User's Wishlist
@app.route("/wishlist/<int:user_id>", methods=["GET"])
def get_user_wishlist(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT cards.* FROM cards
        JOIN wishlist ON cards.id = wishlist.card_id
        WHERE wishlist.user_id = %s;
""", (user_id,))
    wishlist_cards = cursor.fetchall()
    conn.close()
    return jsonify(wishlist_cards)

#remove card from wishlist
@app.route("/wishlist/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wishlist WHERE id = %s", (item_id))
    wishlist_item = cursor.fetchone()
    if not wishlist_item:
        conn.close()
        return jsonify({"error": "Wishlist item not found"}), 404
    cursor.execute("DELETE FROM wishlist WHERE id = %s", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Wishlist item deleted"})

#Get User's Collection
@app.route('/user_cards/<int:user_id>',methods=['GET'])
def get_user_cards(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT cards.* FROM cards
        JOIN user_cards ON cards.id = user_cards.card_id
        Where user_cards.user_id = %s;
    """, (user_id,))
    user_cards = cursor.fetchall()
    conn.close()
    return jsonify(user_cards)

#remove a user profile aka delete profile
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM user_cards WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "user deleted successfully"})


if __name__ == '__main__':
    app.run(debug=True)



