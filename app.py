from flask import Flask,redirect, url_for,render_template, request,session,flash,request
from flask_wtf import FlaskForm
from flask_socketio import SocketIO,send
from wtforms import StringField , PasswordField,SubmitField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired,Length, Email , EqualTo, ValidationError
from flask_login import LoginManager, UserMixin, login_user,current_user,logout_user,login_required
from wtforms.widgets import TextArea
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ROHIT'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
socketio=SocketIO(app)

class User(db.Model , UserMixin):
    id = db.Column(db.Integer,primary_key= True)
    username = db.Column(db.String(15), unique= True, nullable = False)
    email = db.Column(db.String(120), unique= True, nullable = False)

    password = db.Column(db.String(60), nullable = False)



class Usermessagesallchat(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key= True)
    usernameTO = db.Column(db.String(70))
    usernameFROM = db.Column(db.String(70))
    messages = db.Column(db.String(700))
    date_posted = db.Column(db.DateTime, default = datetime.utcnow )





@login_manager.user_loader
def load_user(user_id):
    return (User.query.get(int(user_id)))

class RegistrationForm(FlaskForm):

    username = StringField('UserName' , validators = [DataRequired() , Length(min = 3, max = 14)])
    email = StringField('Email' , validators = [DataRequired() , Email()])
    password = PasswordField('Password' , validators = [DataRequired()])
    Confirm_password = PasswordField('Confirm Password' , validators = [DataRequired() , EqualTo('password')])
    submit = SubmitField('Sign Up!')


class LoginForm(FlaskForm):
    email = StringField('Email' , validators = [DataRequired() , Email()])
    password = PasswordField('Password' , validators = [DataRequired()])

    submit = SubmitField('Log in.')

class MessageForm(FlaskForm):
    usernameTO = StringField('Username' , validators = [DataRequired() ])
    message = StringField('Write-Up' ,validators = [DataRequired()], widget = TextArea())
    submit = SubmitField('Send')


@app.route("/")
def index():

    return render_template("landingpage.html")
@app.route("/about")
def about():

    return render_template("about.html")

@app.route("/home")
@login_required
def mainhome():

    return render_template("mainhomepage.html")


@app.route("/colorburster")
@login_required
def colorburster():

    return render_template("playwithcolors.html")

@app.route("/inbox")
@login_required
def inbox():
    usermsgs=Usermessagesallchat.query.filter_by(usernameTO = current_user.username).all()
    usermsgs.reverse()

    return render_template("inbox.html",inbox = usermsgs)

@app.route("/towerblock")
@login_required
def towerblock():

    return render_template("tower.html")

@app.route("/cube")
@login_required
def cube():

    return render_template("cube.html")

@app.route("/register", methods = ['GET' , "POST"] )

def register():

    form = RegistrationForm()

    if (form.validate_on_submit()):
        ##hashing passwords
        hashed_pwd = form.password.data
        user = User(username = form.username.data ,email = form.email.data, password = hashed_pwd)
        u = form.username.data
        e = form.email.data
        user1 = User.query.filter_by(username =  u ).first()
        user2 = User.query.filter_by(email = e).first()

        if (user1 or user2):
            return ("<h1> Credentials already taken!  </h1>")
        else:
            db.session.add(user)
            db.session.commit()

            flash('Your account has been created, Login!' , 'success')
            return redirect(url_for('login'))

    else:
        return render_template('register.html' ,type ='Register', title = 'Register' , form = form )

@app.route("/message" , methods = ['GET','POST'])
@login_required
def message():
    userlist=[]
    out=[]
    p=False
    form = MessageForm()
    userlist = User.query.with_entities(User.username).all()
    for t in userlist:
        for x in t:
            out.append(x)


    if (form.validate_on_submit()):
        form.usernameTO.data = form.usernameTO.data.strip()
        print(form.usernameTO.data)

        if(form.usernameTO.data==current_user.username):
            return (" <h2> Please select an appropriate username of the username </h2>")

        for i in range(len(out)):
            if(out[i]==form.usernameTO.data):
                p=True
                break
        if(p):
            usermsg = Usermessagesallchat(usernameTO = form.usernameTO.data, usernameFROM = current_user.username, messages = form.message.data)
            db.session.add(usermsg)
            db.session.commit()
            form.usernameTO.data=None
            form.message.data=None
            return render_template("returnMessage.html")
        else:
            return("Please enter a valid username")

    return render_template("message_chats.html",form=form,userlist=out)




@app.route("/login" , methods = ['GET' , "POST"])

def login():
    if (current_user.is_authenticated):
        return redirect(url_for('mainhome'))

    form = LoginForm()
    if (form.validate_on_submit() ):
        user = User.query.filter_by(email = form.email.data).first()
        if(user and (user.password == form.password.data)):
            login_user(user , remember = False)
            next_page = request.args.get('next')
            return redirect(next_page) if (next_page) else (redirect(url_for('mainhome')))
        else:
            return ("<br> <h1>You have entered wrong credentials for Logging in.</h1><br> <p>Go back and    Log in Again! </p>")

    else:
        return render_template('login.html' , type = 'Log in', title = 'Log in',form = form )




login_manager.login_view  = 'login'
login_manager.login_message_category = 'info'


@app.route("/loggedout" )
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/userprofile")
@login_required
def userprofile():
    username= current_user.username
    email= current_user.email
    password= current_user.password

    return render_template("profile.html",username=username,email=email,Password=password)


@app.route("/chat" )
@login_required
def chat():
    if current_user.is_authenticated:
        return render_template("chat.html")

    return "Not Logged in"


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    print(request.sid)

    json["user_name"] =   current_user.username
    if(json["message"].strip() == ""):
        return
        #json["message"] =  "<code> Blank Message </code>"
    #print(json["message"])

    #usr = json['user_name']

    #print(usr)
#    user_1 = Usermessagesallchat(username=usr,messages=msg)
#    db.session.add(user_1)
#    db.session.commit()

    socketio.emit('my response', json, callback=messageReceived)


@app.errorhandler(404)

def not_found(e):
    return render_template("error404.html")

@app.errorhandler(500)
def notatall_found(e):
    return render_template("error500.html")



if __name__ == '__main__':
    socketio.run(app,debug=True)
