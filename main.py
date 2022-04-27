from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room
import json as JSON
import random, string, time

app = Flask(__name__)
app.secret_key = "ThisIsASecretKey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3" # 'users' is the name of the sqlite file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#app.permanent_session_lifetime = timedelta(seconds=30)
app.permanent_session_lifetime = timedelta(days=30)
app.jinja_env.filters['zip'] = zip
socketio = SocketIO(app)

db = SQLAlchemy(app)

class users(db.Model):  # create new table in database 'users'
    _id = db.Column("id", db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    friendcode = db.Column(db.String(6))
    username = db.Column(db.String(100))

    def __init__(self, email, password, friendcode, username):
        self.email = email
        self.password = password
        self.friendcode = friendcode
        self.username = username

class friendsDB(db.Model): # create new table in database 'friendsDB'
    _id = db.Column("id", db.Integer, primary_key=True)
    person1 = db.Column(db.String(6))
    person2 = db.Column(db.String(6))

    def __init__(self, person1, person2):
        self.person1 = person1
        self.person2 = person2

class chat_logs(db.Model): # create new table in database 'chatLogs'
    _id = db.Column("id", db.Integer, primary_key=True)
    sender = db.Column(db.String(6))
    receiver = db.Column(db.String(6))
    timestamp = db.Column(db.String(100))
    msg_content = db.Column(db.String(300))

    def __init__(self, sender, receiver, timestamp, msg_content):
        self.sender = sender
        self.receiver = receiver
        self.timestamp = timestamp
        self.msg_content = msg_content

@app.route("/registration/", methods=["POST", "GET"])
def registration():
    username = None
    if "email" in session:
        email = session["email"]
        found_email = users.query.filter_by(email=email).first()
        if found_email.username == None:
            if request.method == "POST":
                counter = 1 # Counter for while to check whether friend code exists or not
                friendcode = ""
                while counter == 1:
                    def get_random_string(length): # Generate random string for "friend" code
                        letters = string.ascii_uppercase
                        result_str = ''.join(random.choice(letters) for i in range(length))
                        return result_str

                    CheckIfCodeExists = get_random_string(6)
                    found_friendcode = users.query.filter_by(friendcode=CheckIfCodeExists).first()
                    if found_friendcode:
                        continue
                    else:
                        friendcode = CheckIfCodeExists
                        counter = 0
                        break

                session["friendcode"] = friendcode
                username = request.form["username"]
                session["username"] = username
                found_email.username = username
                found_email.friendcode = friendcode
                db.session.commit()
                print("Username saved")
                return redirect(url_for("home"))
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))


    return render_template("registration.html")

@app.route("/friends/", methods=["POST", "GET"])
def friends():
    if "email" in session:
        email = session["email"]
        found_email = users.query.filter_by(email=email).first()
        if found_email.username == None:
            return redirect(url_for("registration"))
        else:

            friendsNameArray = []
            friendsFriendCodeArray = []

            checkFriendsColumnOne = friendsDB.query.filter_by(person1=found_email.friendcode).all()
            checkFriendsColumnTwo = friendsDB.query.filter_by(person2=found_email.friendcode).all()

            for i in checkFriendsColumnOne:
                friendsFriendCodeArray.append(i.person2)

            for j in checkFriendsColumnTwo:
                friendsFriendCodeArray.append(j.person1)

            for o in friendsFriendCodeArray:
                x = users.query.filter_by(friendcode=o).first()
                friendsNameArray.append(x.username)

            if request.method == "POST":
                friendAddCode = request.form["friendAddCode"]

                if friendAddCode == "" or friendAddCode == None:
                    flash("You need to input a code below.")
                elif friendAddCode == found_email.friendcode:
                    flash("You can't add yourself as a friend.")
                else:
                    person1 = found_email.friendcode
                    person2 = friendAddCode

                    checkIfAreFriends1 = friendsDB.query.filter_by(person1=person1).filter_by(person2=person2).first()
                    checkIfAreFriends2 = friendsDB.query.filter_by(person1=person2).filter_by(person2=person1).first()

                    if checkIfAreFriends1 or checkIfAreFriends2:   # If 'checkIfAreFriends' returns something, that means they are friends
                        flash("You are already friends with this person!")
                    else:
                        frd = friendsDB(person1, person2)
                        db.session.add(frd)
                        db.session.commit()
                        flash("Friend added!")

            friendcode = found_email.friendcode
            username = found_email.username
            return render_template("friends.html", friendcode=friendcode, username=username, friendsNames=friendsNameArray, friendsCodes=friendsFriendCodeArray)
    else:
        return redirect(url_for("registration"))

@app.route("/logout/")
def logout():
    if "email" in session:
        flash("You have been logged out.")
    session.pop("email", None)
    session.pop("password", None)
    session.pop("friendcode", None)
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route("/", methods=["POST", "GET"])
@app.route("/home/", methods=["POST", "GET"])
def home():
    if "email" in session: # if user is in session
        email = session["email"]
        found_email = users.query.filter_by(email=email).first()
        if found_email.username == None: # if user registered, but didn't get the chance to add their name
            return redirect(url_for("registration"))
        else: # if user registered and already created a name
            friendsNameArray = []
            friendsFriendCodeArray = []

            checkFriendsColumnOne = friendsDB.query.filter_by(person1=found_email.friendcode).all()
            checkFriendsColumnTwo = friendsDB.query.filter_by(person2=found_email.friendcode).all()

            for i in checkFriendsColumnOne:
                friendsFriendCodeArray.append(i.person2)

            for j in checkFriendsColumnTwo:
                friendsFriendCodeArray.append(j.person1)

            for o in friendsFriendCodeArray:
                x = users.query.filter_by(friendcode=o).first()
                friendsNameArray.append(x.username)

            return render_template("home.html", friendsNames=friendsNameArray, friendsCodes=friendsFriendCodeArray)
    else: # if user is not logged in, show them registration page instead
        if request.method == "POST":
            session.permanent = True
            emailBeforeLower = (request.form["email"])
            email = emailBeforeLower.lower()
            password = request.form["password"]
            session["email"] = email
            session["password"] = password

            # if user didn't put anything for email or password, pop the session and make them restart
            if emailBeforeLower == None or password == None or emailBeforeLower == "" or password == "":
                session.pop("email", None)
                session.pop("password", None)
                session.pop("friendcode", None)
                session.pop("username", None)
                flash("Please enter your details below.")
            else:
                found_email = users.query.filter_by(email=email).first()

                if found_email:
                    if password == found_email.password:
                        print("Password match")
                        if found_email.username == None:
                            return redirect(url_for("registration"))
                        else:
                            return redirect(url_for("home"))
                    else:
                        flash("Password does not match with this account.")
                else:
                    usr = users(email, password, "", None)
                    db.session.add(usr)
                    db.session.commit()
                    print("New account registered")
                    return redirect(url_for("registration"))

        return render_template("login.html")

@socketio.on("connected")
def connected():
    email = session["email"]
    found_email = users.query.filter_by(email=email).first()
    sender = found_email.friendcode
    print(sender, "connected")
    join_room(sender)

@socketio.on("update_other_user")
def update_other_user_func(json):
    getJSON = JSON.dumps(json)
    parseJSON = JSON.loads(getJSON)

    print("IM HERE")
    socketio.emit('get_live_messages', json, room=parseJSON["currentActiveUser"])

@socketio.on("get_active_user") # get the user selected and display the chat messages
def get_active_user_in_list(json, methods=["GET", "POST"]):
    try:
        getJSON = JSON.dumps(json)
        parseJSON = JSON.loads(getJSON)
        if(parseJSON["active"] != ""):
            email = session["email"]
            found_email = users.query.filter_by(email=email).first()
            sender = found_email.friendcode
            receiver = parseJSON["active_user"]

            senderSent =chat_logs.query.filter_by(sender=sender,receiver=receiver).all()
            receiverSent = chat_logs.query.filter_by(sender=receiver,receiver=sender).all()

            msg = []

            for i in senderSent:
                msg.append([int(i.timestamp), i.msg_content, 'sender'])

            for i in receiverSent:
                msg.append([int(i.timestamp), i.msg_content, 'receiver'])

            # Sort messages no matter sent or receive in chronological order, making it easier to pass to javascript
            msg_sort = sorted(msg, key=lambda time: time[0])

            socketio.emit("display_msg", msg_sort, room=sender)
            return receiver
    except KeyError:
        print("KeyError in get_active_user")

@socketio.on('send_msg')
def message_from_user_to_server(json, methods=['GET', 'POST']):
    try:
        getJSON = JSON.dumps(json)
        parseJSON = JSON.loads(getJSON)
        if(parseJSON["chatMessage"] != ""): # Save the message to chat_logs database

            # define variables before push to database
            email = session["email"]
            found_email = users.query.filter_by(email=email).first()
            sender = found_email.friendcode
            receiver = parseJSON["receiver"]
            timestamp = int(round(time.time() * 1000))
            msg_content = parseJSON["chatMessage"]

            chat_log_push = chat_logs(sender, receiver, timestamp, msg_content)
            db.session.add(chat_log_push)
            db.session.commit()
            socketio.emit('receive_post_sent_msg', json, room=sender)
    except KeyError:
        print("KeyError in send_msg")

if __name__ == "__main__":
    db.create_all()
    socketio.run(app, debug=True)
    #app.run(debug=True)
