import json
from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from sqlalchemy.exc import IntegrityError
from datetime import timedelta 

from models import db, User, shopList

def create_app():
  app = Flask(__name__)
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
  app.config['SECRET_KEY'] = "MYSECRET"
  app.config['JWT_EXPIRATION_DELTA'] = timedelta(days = 7) 
  db.init_app(app)
  return app

app = create_app()

app.app_context().push()
db.create_all(app=app)

def authenticate(uname, password):
  user = User.query.filter_by(username=uname).first()
  if user and user.check_password(password):
    return user

def identity(payload):
  return User.query.get(payload['identity'])

jwt = JWT(app, authenticate, identity)

@app.route('/')
def index():
  return " Working... "

@app.route('/identify')
@jwt_required()
def protected():
    return json_dumps(current_identity.username)


@app.route('/signup', methods=['POST'])
def signup():
  userdata = request.get_json() 
  newuser = User(username=userdata['username'], email=userdata['email'])
  newuser.set_password(userdata['password']) 
  try:
    db.session.add(newuser)
    db.session.commit() 
  except IntegrityError:
    db.session.rollback()
    return 'Username/Email account already exists'
  return 'User created successfully'


@app.route('/shoplist', methods=['POST'])
@jwt_required()
def create_shoppingList():
  data = request.get_json()
  shoplist = shopList(text=data['text'], userid=current_identity.id, done=False)
  db.session.add(shoplist)
  db.session.commit()
  return json.dumps(shoplist.id), 201 

@app.route('/shoppinglist', methods=['GET'])
@jwt_required()
def get_shoppingLists():
  shoppinglist = shopList.query.filter_by(userid=current_identity.id).all()
  shoppinglist = [shopList.toDict() for shopList in shoppinglist] 
  return json.dumps(shoppinglist)


@app.route('/slist/<id>', methods=['GET'])
@jwt_required()
def get_list(id):
  slist = shopList.query.filter_by(userid=current_identity.id, id=id).first()
  if slist == None:
    return 'Invalid id or unauthorized'
  return json.dumps(slist.toDict())

@app.route('/gsList/<id>', methods=['PUT'])
@jwt_required()
def update_shopplingList(id):
  gsList = shopList.query.filter_by(userid=current_identity.id, id=id).first()
  if gsList == None:
    return 'Invalid id or unauthorized'
  data = request.get_json()
  if 'text' in data: 
    gsList.text = data['text']
  if 'done' in data:
    gsList.done = data['done']
  db.session.add(gsList)
  db.session.commit()
  return 'Updated', 201

@app.route('/dlist/<id>', methods=['DELETE'])
@jwt_required()
def delete_shoppingList(id):
  dlist = shopList.query.filter_by(userid=current_identity.id, id=id).first()
  if dlist == None:
    return 'Invalid id or unauthorized'
  db.session.delete(dlist) 
  db.session.commit()
  return 'Deleted', 204


app.run(host='0.0.0.0', port=8080)