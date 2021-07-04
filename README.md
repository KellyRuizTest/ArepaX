# Arepacoin Exchange
#### Video Demo: [Demo](http:)
#### Description:

##### Basically my project is a exchange Cryptocurrency where you can:

* Register 
* Login
* Check prices and status 
* Buy
* Sell
* Track history
* Management your portfolio of Cryptocurrency
* Funding Account 


To do that I use flask MVC framework for Web development which knowledge was acquired in the course,
Also use MySQL for creating Database, Tables and querys logic, in order to get info about Crypto currency I connect to an API and finally in the front end was built using bootstrap library HTML/CSS and a little Javascript for some interactive form.

#### Logic app.py
Let me explain step by step methods in the logic:

- **method index()** this method only render web page presentation 

- **method home()** this method connect to the API to get info for each crypto (like price, name, ticker, logo etc) after that create a table to store that cryptocurrencies and after parse info send to html (view) to be shown in a table 

- **method register()** basically save info from the form (view) and store that info in a table in the Database called users, just to mention that $10000 are added to any user in the register profile and some column like fullname, phone and address are null by default in order to update later.

- **method login()** basically check information getting from the view (form) and compare in Database password 

- **method logout()** has to intent clear all information in session variable in order to logout and redirect to login view

- **method password()** changing password for any user that needs to change it.

- **method profile()** this method has to intent to update information for fullname, address and phone for any user and show info in view profile.html

- **method funding()** this method render a form to fund account by credit card, this method only take value in the input cash and dont check if credit card is real or correct (only for academy purposes) but it is a simulation process to add cash in your account.

- **method history()** this method get information thru query from history table which already stored all transaction with crypto currencies in the web app, transaction like sell or buy are stored and the information stored are: price, ticker, date, type (sell or buy), quantity of coin (sold o bought)


- **method histofun()** this method get information about any fund performed by the user in the app

- **method portfolio()** render a view with two important sections, first a chart to see graphic coins and % weight that represents each coin in the portfolio. Second a table with each coin qantity and its value calculated in USD

- **method buy()** this method has to intend to buy a coin, the algorithm here is:  first get info related to the user like cash, from the view select coins available to buy, from the API get current price in real time, check if cash is posible to buy quantity of coin that you want, insert a new row in the table history, insert a new row in the table portfolio, update cash available for the user, finally render to portfolio view.

- **method sell()** this method has to intend to sell a coin, the algorithm here is: first get cash available for the user, get all coins in the portfolio and send to view to fill dropdown list, getting from the POST request quantity coin and the name of coin that want to sell, from the API get the current value of that coin, update quantity coin of that coin that will be sold, update cash for the user.


#### views 

- **home.html** view to be render in method home() and intend to show a table of coins available to trade and un button to funding account
- **index.html** Front end in HTML/CSS that show feature about the web app
- **funding.html** view to be render in method funding() and its intend is to add cash thru a form
- **histoy.html** view that shows a table for all trades made sells and buys
- **histofun.html** view that shows a table for all funding performed in the account.
- **login.html** view to render form to be log in 
- **register.html** view to render a form to be register a new user
- **profile.html** view that show all information about the user already logged.
- **password.html** view that show a form and its intend to change password.
- **buy.html** this view show a form where a dropdown list that all coins available to buy, show cash available to perform the buy.
- **sell.html** this view show a list from coins in the portfolio table and show that dropdown list and quantities of coin in portfolio.
- **portfolio.html** this view show a chart made by chart.js and a table with all coins and weight in the portfolio for the user.

#### table 

- **table coins** this table store all coin available got from the API. columns: id, name, ticker, logo for each coin.
- **table funding** this table store all funding history. columns: id, cash_actual, funding (amount of cash), date.
- **table users** this table store all users in the app and its columns are: id, fullname, email, password, cash (by deafult get $10,000 USD), phone.
- **table history** this table store all trades sells and buys.
- **table portfolio** this table store all coins using a colum id can be related to the user and its columns are: id, id_user, ticker, name, price, qty_coins, logo, date.

