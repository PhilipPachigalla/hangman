import os
import datetime
import plaid
import random
from flask import Flask
from flask import session
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect


app = Flask(__name__)
app.secret_key = "v8rffXDFHFDHwncmcnWWnLCA"

# Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
PLAID_SECRET = '0cfa5cb2ad4c45406ac3ad5e06c9b6'
PLAID_CLIENT_ID = '58c1d89e4e95b878627b305e'
PLAID_PUBLIC_KEY = 'ca5343eec262eadc7bea9fad10d6e8'
# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use `development` to test with live users and credentials and `production`
# to go live
PLAID_ENV='development'


client = plaid.Client(client_id = PLAID_CLIENT_ID, secret=PLAID_SECRET,
                  public_key=PLAID_PUBLIC_KEY, environment=PLAID_ENV)

@app.route("/")
def index():
   return render_template('index.ejs', plaid_public_key=PLAID_PUBLIC_KEY, plaid_environment=PLAID_ENV)


access_token = None
public_token = None

@app.route("/get_access_token", methods=['POST'])
def get_access_token():
  global access_token
  public_token = request.form['public_token']
  exchange_response = client.Item.public_token.exchange(public_token)
  print 'access token: ' + exchange_response['access_token']

  access_token = exchange_response['access_token']

  return jsonify(exchange_response)

@app.route("/set_access_token", methods=['POST'])
def set_access_token():
  global access_token
  access_token = request.form['access_token']
  print 'access token: ' + access_token
  return jsonify({'error': False})


@app.route("/item", methods=['GET', 'POST'])
def item():
  global access_token
  item_response = client.Item.get(access_token)
  institution_response = client.Institutions.get_by_id(item_response['item']['institution_id'])
  return jsonify({'item': item_response['item'], 'institution': institution_response['institution']})

@app.route("/transactions", methods=['GET', 'POST'])
def transactions():
  global access_token
  global trans
  # Pull transactions for the last 30 days
  start_date = "{:%Y-%m-%d}".format(datetime.datetime.now() + datetime.timedelta(-90))
  end_date = "{:%Y-%m-%d}".format(datetime.datetime.now())

  response = client.Transactions.get(access_token, start_date, end_date)
  transactions = response['transactions']
  Names = []
  for i in transactions:
    name = i['name']
    name = name.upper()
    if "-" in name:
        name = name.replace("-", " ")
    names_list = name.split(" ")
    names_list = names_list[:3]

    for word in names_list:
      if has_number(word):
        names_list.remove(word)
      elif has_star(word):
        names_list.remove(word)
      elif not (any(vowel in word for vowel in ["A", "E", "I", "O", "U"])):
        names_list.remove(word)


      if len(names_list) == 0:
        continue
      
    name = " ".join(names_list)
    Names.append((name, i['amount'], i['date']))

  trans = Names
  return jsonify(response)

@app.route("/create_public_tokens", methods=['GET'])
def create_public_token():
  global access_token
  # Create a one-time use public_token for the Item. This public_token can be used to
  # initialize Link in update mode for the user.
  response = client.Item.public_token.create(access_token)
  return jsonify(response)



def has_number(S):
  for i in S:
    if i.isdigit():
      return True
  return False

def has_star(S):
  return "*" in S

class Game():
  def __init__(self, word, nextTrans, amount, date):
    self.playing = True
    self.word = word
    self.nextTrans = nextTrans
    self.amount = amount
    self.date = date
    self.tried = []
    self.mistakes = [i for i in self.tried if i not in self.word]  
    self.current = "".join([i if i in self.tried else "_" for i in self.word])
    self.lenM = 0
    
  

  def try_letter(self, letter):
    if self.playing and letter not in self.tried:
      self.tried.append(letter)

    self.mistakes = [i for i in self.tried if i not in self.word]  
    self.current = "".join([i if i in self.tried else "_" for i in self.word])
    self.lenM = len(self.mistakes)
    self.over = self.win() or self.lose()
    self.lost = self.lose()
    self.won = self.win()

  def win(self):
    return self.current == self.word

  def lose(self):
    return len(self.mistakes) == 6

  
  @app.route("/play")
  def new_game():
    global game
    n = random.randint(0, len(trans)-2)
    word, amount, date = trans[n]
    nextTrans = trans[n+1][0]
    game = Game(word, nextTrans, amount, date)
    if " " in game.word:
      game.try_letter(" ")
    elif "'" in game.word:
      game.try_letter("'")
    return redirect("/playing")
  
  
  @app.route("/playing", methods=['GET', 'POST'])
  def playing():
    global game
    if request.method == 'POST':
      letter = request.form['letter'].upper()
      if len(letter) == 1 and letter.isalpha():
        game.try_letter(letter)

    
    if request.is_xhr:
      return flask.jsonify(current = game.current, mistakes=game.mistakes, playing = game.playing)
    
    else:
      return render_template("game.html", game=game)

if __name__ == "__main__":
    app.run()
