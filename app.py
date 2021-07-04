from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, BooleanField, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from helpers import checkAPI, checkAPI_info, checkAPI_byid, checkAPI_byid_latest

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'projectcs50'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)

#Custom filter
#app.jinja_env.filters["usd"] = usd

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/home')
def home():
    # called to API to get crypto info
    result_crypto = checkAPI()
    
    # list to retrieve from API info about first 10 cryptos
    list_cryptos = []

    # list to store only id to use in other request to API
    list_id = []

    # MySQL connection
    cur = mysql.connection.cursor()

    # CREATE TABLE to store coins to use later 
    cur.execute("CREATE TABLE IF NOT EXISTS coins (id INT AUTO_INCREMENT PRIMARY KEY, id_coin TEXT NOT NULL, name TEXT NOT NULL, ticker TEXT NOT NULL, logo TEXT NOT NULL)")

    # getting data as name, price, symbol etc.
    for row in result_crypto["data"]:

        quote = row["quote"]
        new_crypto = {
            "id": row["id"],
            "name" : row["name"],
            "ticker" : row["symbol"],
            "price" : round(quote["USD"]["price"], 2),
            "change" : round(quote["USD"]["percent_change_24h"], 2),
            "market_cap": round(quote["USD"]["market_cap"], 2)
        }
        list_id.append(row["id"])
        list_cryptos.append(new_crypto)
        del new_crypto


    # called to API to get info where is logo for each id
    results_logo = checkAPI_info(list_id)
    #print(results_logo)
        
    i = 0
    final_crypto = []
    for anyrow in list_cryptos:
        anyrow["logo"] = str(results_logo[i])
        #print(anyrow)
        final_crypto.append(anyrow)
        i = i + 1

    result_coins = cur.execute("SELECT * from coins")

    print(result_coins)
    
    
    if not result_coins > 1:
        print("I am into the IF")
        
        for i in range(len(final_crypto)):
            idcoin=final_crypto[i]["id"]
            namecoin=final_crypto[i]["name"]
            tickercoin=final_crypto[i]["ticker"]
            logocoin=final_crypto[i]["logo"]
            cur.execute("INSERT INTO coins(id_coin, name, ticker, logo) VALUES(%s, %s, %s, %s)", (idcoin, namecoin, tickercoin, logocoin))
            mysql.connection.commit()

    cur.close()
    return render_template("home.html", final_crypto=final_crypto)

# User register
@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        if password != confirm:
            flash('Not registered! Password should be same!', 'danger')
            return redirect("/register")

        password = sha256_crypt.encrypt(str(request.form.get("password")))
        confirm = sha256_crypt.encrypt(str(request.form.get("confirmation")))

        #Create cursor
        cur = mysql.connection.cursor()

        already_created = cur.execute("SELECT * FROM users WHERE email = %s", [email])

       # print(already_created)

        if already_created > 0:
            flash('Email already exists!', 'danger')
            return redirect("/register")

        cur.execute("INSERT INTO users(username, email, hash) VALUES(%s, %s, %s)", (username, email, password))

        # Commit to DB
        mysql.connection.commit()

        # Close 
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect("/home")

        #return render_template("register.html", form =form)
    else:
        return render_template("register.html")


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():

    session.clear()

    if request.method == 'POST':
        # Get Form fields
        email = request.form.get('email')
        password_candidate = request.form.get('password')

        # Create Cursor
        cur = mysql.connection.cursor()

        # Get  user by username
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['hash']
            iduser = data['id']

            #print(iduser)
            #print(email)

            # Compare passwords
            if sha256_crypt.verify(password_candidate, password):

                #create session variables
                session['logged_in'] = iduser
                session['username'] = data['username']

                flash('You are now logged in', 'success')
                return redirect("/home")

            else:
                flash('Password Incorrect!', 'danger')
                return render_template('login.html')
            
            # Close connection
            cur.close()

        else:
            flash('User not found', 'danger')
            return render_template('login.html')     

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
        
    return wrap

@app.route('/academy')
def about():
    return render_template('academy.html')


# changin password
@app.route('/password', methods=['GET', 'POST'])
@is_logged_in
def password():

    #Create cursor
    cur = mysql.connection.cursor()

    userdata = user = cur.execute("SELECT * FROM users WHERE id = %s", [session['logged_in']])
    data = cur.fetchone()
    password = data['hash']

    if request.method == 'POST':
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm = request.form.get("confirm")

        if sha256_crypt.verify(old_password, password):
            
            if (new_password == confirm):

                final_password = sha256_crypt.encrypt(str(new_password))
                cur.execute("UPDATE users SET hash=%s WHERE id=%s", (final_password, str(session['logged_in'])))
                mysql.connection.commit()

                flash("Password updated!", 'success')
                return redirect("/home")

            else:
                flash("New password and Confirm password does not match!", 'danger')
                return render_template('password.html')
        else:
            flash("Password Invalid!", 'danger')
            return render_template('password.html')

    return render_template('password.html')

@app.route('/buy', methods=['GET', 'POST'])
@is_logged_in
def buy():

    #Create cursor
    cur = mysql.connection.cursor()
    
    # Get  user by username
    user = cur.execute("SELECT * FROM users WHERE id = %s", [session['logged_in']])
    data = cur.fetchone()
    available = float(data['cash'])
    print(available)

    # Get all coins available
    resultcoins = cur.execute("SELECT * FROM coins")
    global_list = cur.fetchall()

    if request.method == 'POST':

        # How much coin will buy and How much money will spend
        money_spend = float(request.form.get("cantidad_usd"))
        coin_buy = request.form.get("shares")

        coin_buy = coin_buy.strip()

        # Getting data of buy that I want to buy
        cur.execute("SELECT * FROM coins WHERE ticker=%s", [coin_buy])
        info_coin_buy = cur.fetchone()

        # Getting data updated from API of coin to buy
        resultapi = checkAPI_byid_latest(info_coin_buy["id_coin"])
        quoteaux = resultapi["quote"]
        
        #print(quoteaux)

        # price & quantity of coins (for the case of Bitcoin will be sats or Bitcoins)
        price = float(quoteaux["USD"]["price"])
        #print(price)

        qty_coins = round(money_spend / price, 6)
        #print(qty_coins)

        if (available - money_spend > 0):
            total_available = available - money_spend

            # update cash for users account
            cur.execute("UPDATE users SET cash=%s WHERE id=%s", (str(total_available), str(session['logged_in'])))
            mysql.connection.commit()

            # validation if table of history exists if not proced to create
            cur.execute("CREATE TABLE IF NOT EXISTS history (id_hist INT AUTO_INCREMENT PRIMARY KEY, id INT NOT NULL, ticker TEXT NOT NULL, name TEXT NOT NULL, price FLOAT NOT NULL, qty_coins FLOAT NOT NULL, id_coin TEXT NOT NULL, type TEXT NOT NULL, transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(id) REFERENCES users(id) )")

            # validation if table of portfolio exists if not proced to create
            cur.execute("CREATE TABLE IF NOT EXISTS portfolio (id_port INT AUTO_INCREMENT PRIMARY KEY, id INT NOT NULL, ticker TEXT NOT NULL, name TEXT NOT NULL, price FLOAT NOT NULL, qty_coins FLOAT NOT NULL, id_coin TEXT NOT NULL, logo TEXT NOT NULL, transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(id) REFERENCES users (id))")

            # Get any register if already has the coin in the portfolio
            ifexist_coin = cur.execute("SELECT * FROM portfolio WHERE id=%s AND id_coin=%s", (session['logged_in'], str(info_coin_buy["id_coin"])) )
            qty_coins_fromdb = cur.fetchone()

            iflogo = cur.execute("SELECT * FROM coins WHERE id_coin=%s", [info_coin_buy["id_coin"]])
            logo_coin = cur.fetchone()

            #print(logo_coin["logo"])

            # If row > 0 need to sum new purcharse to coin stored in portfolio
            if ifexist_coin > 0:
                total_coin = qty_coins + float(qty_coins_fromdb["qty_coins"])
                print(qty_coins_fromdb["qty_coins"])
                print(total_coin)
                cur.execute("UPDATE portfolio SET qty_coins=%s WHERE id=%s AND id_coin=%s", (total_coin, session['logged_in'], info_coin_buy["id_coin"]))
                mysql.connection.commit()
            else:
                cur.execute("INSERT INTO portfolio(id, ticker, name, price, qty_coins, id_coin, logo) VALUES(%s, %s, %s, %s, %s, %s, %s)", (session['logged_in'], info_coin_buy["ticker"], info_coin_buy["name"], price, qty_coins, info_coin_buy["id_coin"], logo_coin["logo"]))
                mysql.connection.commit()

            # Insert new transaction in the history 
            cur.execute("INSERT INTO history(id, ticker, name, price, qty_coins, id_coin, type) VALUES(%s, %s, %s, %s, %s, %s, %s)", (session['logged_in'], info_coin_buy["ticker"], info_coin_buy["name"], price, qty_coins, info_coin_buy["id_coin"], "Buy") )
            mysql.connection.commit()
            cur.close()
            flash('Enjoy your bought, see your new portfolio!', 'success')
            return redirect('portfolio')

        else:
            flash('You dont have enough money to buy, Please fund account', 'danger')
            cur.close()
            return render_template('funding.html')
    else:
        cur.close()
        return render_template('buy.html', global_list=global_list, available=available)
        

@app.route("/portfolio", methods=["GET", "POST"])
@is_logged_in
def portfolio():
   
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM portfolio WHERE id=%s", [session['logged_in']])
    current_port = cur.fetchall()

    #print(current_port)

    dict_for_prices = {}
    final_list = []
    dictionary_for_graph = {}

    # cash user
    user_aux = cur.execute("SELECT * FROM users WHERE id=%s", [session['logged_in']])
    userin = cur.fetchone()

    cash = userin['cash']

    # total value in portfolio
    total_value = 0

    for row in current_port:
        pricecheckAPI = row["id_coin"]
        datafromAPI = checkAPI_byid_latest(str(pricecheckAPI))
        actual_price = datafromAPI["quote"]["USD"]["price"]
        value_coin = float(actual_price) * float(row["qty_coins"])

        total_value = round(total_value + value_coin, 2)

        value_coin = str(round(value_coin, 2))

        dict_for_prices = {
            "name" : str(row["name"]),
            "ticker" : str(row["ticker"]),
            "cantidad" : str(row["qty_coins"]),
            "logo" : str(row["logo"]),
            "price" : str(round(actual_price, 2)),
            "value" : value_coin
        }

        dictionary_for_graph[row["ticker"]] = value_coin

        final_list.append(dict_for_prices)
    
    # print and check if dictionary is complete
    print(dictionary_for_graph)
    return render_template('portfolio.html', final_list=final_list, dictionary_for_graph=dictionary_for_graph, total_value=total_value, cash=cash)

@app.route("/histofun", methods=["GET", "POST"])
@is_logged_in
def histofun():
    # cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM funding WHERE id=%s", [session['logged_in']])
    fund_aux = cur.fetchall()

    for row in fund_aux:
        print(row)

    if (len(fund_aux) > 0):
        return render_template('histofun.html',fund_aux=fund_aux)
    else:
        return render_template('nohistofund.html')

    

@app.route("/profile", methods=["GET", "POST"])
@is_logged_in
def profile():
     
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users WHERE id=%s", [session['logged_in']])
    data_profile = cur.fetchone()

    if request.method == 'POST':
        fullname = request.form.get("fullname")
        phone = request.form.get("phone")
        address = request.form.get("address")

        cur.execute("UPDATE users SET address=%s, phone=%s, fullname=%s WHERE id=%s", (address, phone, fullname, [session['logged_in']]) )
        mysql.connection.commit()

        flash('Profile updated', 'success')
        return redirect("/home")

    
    return render_template('profile.html', data_profile=data_profile)

@app.route("/funding", methods=["GET", "POST"])
@is_logged_in
def funding():

    if request.method == 'POST':
        
        # cursor
        cur = mysql.connection.cursor()
        cash_adicional = request.form.get("cashing")
        
        # Getting user info 
        result = cur.execute("SELECT * FROM users WHERE id=%s", [session['logged_in']])
        aux_cash = cur.fetchone()
        cash_available = aux_cash['cash']

        # Compute cash
        total_cash = float(cash_adicional) + float(cash_available)

        # Update new cash
        cur.execute("UPDATE users SET cash=%s WHERE id=%s", (total_cash, session['logged_in']))
        mysql.connection.commit()

        # Create Table if not exists
        cur.execute("CREATE TABLE IF NOT EXISTS funding (id_funding INT AUTO_INCREMENT PRIMARY KEY, id INT NOT NULL, cash_actual FLOAT NOT NULL, funding FLOAT NOT NULL, transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(id) REFERENCES users(id) )")

        # Insert new row in the table
        cur.execute("INSERT INTO funding(id, cash_actual, funding) VALUES(%s, %s, %s)", (session['logged_in'], float(cash_available), float(cash_adicional)) )
        mysql.connection.commit()

        return redirect("/home")

    return render_template('funding.html')


@app.route('/sell', methods=["GET", "POST"])
@is_logged_in
def sell():
    cur = mysql.connection.cursor()
    
    # Get  user by username
    user = cur.execute("SELECT * FROM users WHERE id = %s", [session['logged_in']])
    data = cur.fetchone()
    available = float(data['cash'])

    # Get all coins available
    resultcoins = cur.execute("SELECT * FROM portfolio WHERE id = %s", [session['logged_in']])
    global_list = cur.fetchall()

    #print(global_list)

    # ticker and price 
    list_with_ticker_and_price = {}
    for row in global_list:
        list_with_ticker_and_price[row["ticker"]] = str(row["qty_coins"])

    # When is POST need to get qty_coin to sell and coin from form / input
    if request.method == 'POST':
        qty_to_sell = float(request.form.get("qty_shares"))
        crypto_to_sell = request.form.get("crypto")
        crypto_to_sell = crypto_to_sell.strip()

        only_for_nothing = cur.execute("SELECT * FROM portfolio WHERE id=%s AND ticker=%s", ([session['logged_in']], [crypto_to_sell]))
        coin_to_sell = cur.fetchall()

        disponible_qty_coins = coin_to_sell[0]["qty_coins"]

        # if qty_to_sell > what we have return to home and danger flag sent it
        if (qty_to_sell > disponible_qty_coins):
            flash('You cannot sell quantity that you dont have available', 'danger')
            return redirect('/home')
        else:
        
        # Update portfolio qty_coins and cash available after that
            final_qty_coins = disponible_qty_coins - qty_to_sell
            cur.execute("UPDATE portfolio SET qty_coins=%s WHERE id=%s AND ticker=%s", (final_qty_coins, str(session['logged_in']), crypto_to_sell))
            mysql.connection.commit()
        
        # Getting current price to the coin to sell
            auxiliar = checkAPI_byid_latest(coin_to_sell[0]["id_coin"])
            actual_price_to_sell = auxiliar["quote"]["USD"]["price"]

        # Insert new transaction for selling
            cur.execute("INSERT INTO history(id, ticker, name, price, qty_coins, id_coin, type) VALUES(%s, %s, %s, %s, %s, %s, %s)", (session['logged_in'], coin_to_sell[0]["ticker"], coin_to_sell[0]["name"], actual_price_to_sell, qty_to_sell, coin_to_sell[0]["id_coin"], "Sell") )
            mysql.connection.commit()

        # cash update 
            cash_update = float(actual_price_to_sell) * float(qty_to_sell) + available
            cur.execute("UPDATE users SET cash=%s WHERE id=%s", (cash_update, str(session['logged_in'])))
            mysql.connection.commit()
            flash("Portfolio updated!", 'success')
        return redirect('portfolio')

    else:
        return render_template('sell.html', global_list=global_list, list_with_ticker_and_price=list_with_ticker_and_price)

@app.route('/history')
@is_logged_in
def articles():
    # Create cursor
    cur = mysql.connection.cursor()
    results = cur.execute("SELECT * FROM history WHERE id = %s ORDER BY transacted DESC",[session['logged_in']])
    list_transactions = cur.fetchall()

    # Get articles
    return render_template('history.html', list_transactions=list_transactions)
    

# Logut
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logge out', 'sucess')
    return redirect(url_for('login'))
    

if __name__ == '__main__':
    app.secret_key ='admin123'
    app.run(debug = True)


