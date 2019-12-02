from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time

app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "images")

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="",
                             db="finsta",
                             charset="utf8mb4",
                             port=3306,
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=session["username"])

@app.route("/upload", methods=["GET"])
@login_required
def upload():
    return render_template("upload.html")

@app.route("/images", methods=["GET"])
@login_required
def images():
    query = "SELECT * FROM photo"
    with connection.cursor() as cursor:
        cursor.execute(query)
    data = cursor.fetchall()
    return render_template("images.html", images=data)

@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/createFriendGroup", methods=["GET"])
def createFriendGroup():
    return render_template("createFriendGroup.html")

@app.route("/addToFriendGroup", methods=["GET"])
def addToFriendGroup():
    return render_template("addToFriendGroup.html")

@app.route("/sendfollow", methods=["GET"])
def follow():
    return render_template("sendfollow.html")

@app.route("/A_DFollow", methods=["GET"])
def A_Dfollow():
    return render_template("A_DFollow.html")

#---------------------------------------------------
#LOGIN INFO
@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

        with connection.cursor() as cursor:
            query = "SELECT * FROM person WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashedPassword))
        data = cursor.fetchone()
        if data:
            session["username"] = username
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)

@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
        firstName = requestData["fname"]
        lastName = requestData["lname"]
        biography = requestData["biography"]

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO person VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (username, hashedPassword, firstName, lastName, biography))
        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)    

        return redirect(url_for("login"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)


#--------------------------------------------
#SETTIG UP FRIEND GROUPS AND ADDING THEM, COULD BE MADE TO LOOK NICER LATER
@app.route("/friendGroup", methods=["POST"])
def friendGroup():
    if request.form:
        requestData = request.form
        groupName = requestData["groupName"]
        username = session["username"]
        description = requestData["description"]
        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO friendgroup VALUES (%s, %s, %s)"
                cursor.execute(query, (username, groupName, description))
                query = "INSERT INTO belongto VALUES(%s, %s, %s)"
                cursor.execute(query, (username, username,groupName))

        except pymysql.err.IntegrityError:
            error = "Error try again"
            return render_template('createFriendGroup.html', error=error)    

        return redirect(url_for("home"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)

@app.route("/addToFriendGroup", methods=["POST"])
def addTofriendGroup():
    if request.form:
        requestData = request.form
        groupName = requestData["groupName"]
        username = session["username"]
        friend = requestData["friend"]
        with connection.cursor() as cursor:
            checkinGroupquery = "SELECT * FROM belongto WHERE member_username=%s and groupName=%s"
            cursor.execute(checkinGroupquery, (username, groupName))
            checkinGroupquery = cursor.fetchone()
            checkifAccount = "SELECT * FROM person WHERE username=%s"
            cursor.execute(checkifAccount, (friend))
            checkifAccount = cursor.fetchone()
            if checkifAccount and checkinGroupquery:
                query = "INSERT INTO belongto VALUES (%s, %s, %s)"
                query2 = "SELECT owner_username FROM belongto WHERE groupName=%s AND member_username=%s"
                cursor.execute(query2, (groupName, username) )
                groupOwner = cursor.fetchone()["owner_username"]
                cursor.execute(query, (friend, groupOwner, groupName))
            else: 
                message = "Either you are not in this group, the group does not exist or the friends account can't be found"
                return render_template("addToFriendGroup.html", message = message)
        return redirect(url_for("home"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)
#---------------------------------------
#FOLLOW ACCEPTING AND REJECTING


#This method proccesses the form and validates any query for sending a follow request
@app.route("/sendFollow", methods=["POST"])
@login_required
def sendFollow():
    if request.form:
        requestData = request.form
        followed = requestData["person"]
        follower = session["username"]
        try:
            with connection.cursor() as cursor:
                query = "SELECT * FROM Follow WHERE username_followed=%s AND username_follower=%s"
                cursor.execute(query, (follower, followed))
                followExist = cursor.fetchall()
                if followExist:
                    message = "There is an active request for %s" % (followed)
                    return render_template("follow.html", message=message)
                checkifAccount = "SELECT * FROM person WHERE username=%s"
                cursor.execute(checkifAccount, (followed))
                checkifAccount = cursor.fetchone()
                if checkifAccount:
                    query = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, 0)"
                    cursor.execute(query, (followed, follower))
                else:
                    message = "%s does not exist" % (followed)
                    return render_template("follow.html", message=message)
        except pymysql.err.IntegrityError:
            message = "%s does not exist." % (followed)
            return render_template("follow.html", message=message)
        return redirect(url_for("home"))

#This method proccesses the form and validates any query for sending a follow request
@app.route("/A_DFollow", methods=["POST"])
@login_required
def A_DFollow():
    if request.form:
        requestData = request.form
        followed = requestData["person"]
        follower = session["username"]
        try:
            with connection.cursor() as cursor:
                query = "SELECT * FROM Follow WHERE username_followed=%s AND username_follower=%s"
                cursor.execute(query, (follower, followed))
                followExist = cursor.fetchall()
                if followExist:
                    message = "There is an active request for %s" % (followed)
                    return render_template("follow.html", message=message)
                checkifAccount = "SELECT * FROM person WHERE username=%s"
                cursor.execute(checkifAccount, (followed))
                checkifAccount = cursor.fetchone()
                if checkifAccount:
                    query = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, 0)"
                    cursor.execute(query, (followed, follower))
                else:
                    message = "%s does not exist" % (followed)
                    return render_template("follow.html", message=message)
        except pymysql.err.IntegrityError:
            message = "%s does not exist." % (followed)
            return render_template("follow.html", message=message)
        return redirect(url_for("home"))


#------------------------------------------------
#UPLOADING IMAGES

@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    if request.files:
        requestData = request.form
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)
        username = session["username"]
        caption = requestData["caption"]
        allFollowers = requestData["allFollowers"]
        groupName = requestData["groupName"]
        query = "INSERT INTO photo (postingdate, filepath, allFollowers, caption, photoPoster) VALUES (%s, %s, %s, %s, %s)"
        query1 = "INSERT INTO groupName (groupOwner, groupName, photoID)"
        if (allFollowers == "1"):
            with connection.cursor() as cursor:
                cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name, allFollowers, caption, username))
            message = "Image has been successfully uploaded."
            return render_template("upload.html", message=message)
        else:
            query1 = "INSERT INTO sharedwith (groupOwner, groupName, photoID) VALUES (%s, %s, %s)"
            query2 = "SELECT owner_username FROM belongto WHERE groupName=%s AND member_username=%s"
            with connection.cursor() as cursor:
                cursor.execute(query2, (groupName, username) )
                groupOwner = cursor.fetchone()["owner_username"]
                if groupOwner:
                    query3 = "SELECT photoID FROM photo WHERE photoPoster=%s AND filepath =%s AND postingdate=%s"
                    timeVal = time.strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(query, (timeVal, image_name, allFollowers, caption, username))
                    cursor.execute(query3, (username, image_name, timeVal))
                    photoID = cursor.fetchone()["photoID"]
                    cursor.execute(query1, (groupOwner, groupName, photoID))
                    message = "Image has been successfully uploaded."
                    return render_template("upload.html", message=message)
                else:
                    message = "Either group does not exist or you are not a member of this group"
                    return render_template("upload.html", message=message)
                    
            
            
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")

if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run()
