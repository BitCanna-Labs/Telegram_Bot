import telebot
import requests
import random
import sqlite3
from mytoken import token, PATH, DATABASE
import time
from threading import Thread

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, 'Howdy, how are you doing?')
	bot.reply_to(message, """\
		Commands:\n
		/start or /help -> This help \n
		/stats -> Statistics from the BC blockchain\n
		/price -> CoinGecko prices for BC\n
		/stakingapr -> Get the current Staking APR\n
		/pickvalidator -> Suggest a random validator\n
		\n
		Direct Message Subscriptions:\n
		/subscribe bcna-address -> You will receive alerts when you balance changes
		/mybalance -> Return you current balance for each address subscribed
		/unsubscribe -> You won't receive more alerts
		/subscriptions -> Show you your current addresses to be checked
		""")

# Statistics from the blockchain can be found here, uses different points to collect data and present it in 1 message
@bot.message_handler(commands=['stats'])
def chain_statistics(message):
	baseurl = 'http://seed1.bitcanna.io:1317/'
	blockslatesturl = baseurl+'/cosmos/base/tendermint/v1beta1/blocks/latest'
	validatorsurl = baseurl+'/cosmos/staking/v1beta1/validators'
	activevalidatorsurl = validatorsurl+'?status=BOND_STATUS_BONDED'
	poolurl = baseurl+'cosmos/staking/v1beta1/pool'
	try:
		responseblocks = requests.get(blockslatesturl,headers={'Accept': 'application/json'},)
		responseval = requests.get(validatorsurl,headers={'Accept': 'application/json'},)
		responseactval = requests.get(activevalidatorsurl,headers={'Accept': 'application/json'},)
		responsepool = requests.get(poolurl,headers={'Accept': 'application/json'},)
	except requests.exceptions.RequestException:
		bot.reply_to(message,'Connection error, the API is currently not working. Please try again later.')
	else:
		datablock = responseblocks.json()
		datavalidators = responseval.json()
		dataactval = responseactval.json()
		datapool = responsepool.json()
		latestblockjson = datablock['block']
		
		latestblock = latestblockjson['header']['height']
		activevalidators = dataactval['pagination']['total']
		validatorlist = datavalidators['validators']
		validatorjailed = []
		
	
		for validator in validatorlist:
			validator_name = validator['description']['moniker']
			
			if validator['jailed'] == True:
				validatorjailed.append(validator_name)
			elif validator['jailed'] == False:
				pass
		
		unbonding = int(datapool['pool']['not_bonded_tokens']) / 1000000
		bonded = int(datapool['pool']['bonded_tokens']) / 1000000
		percentage_bonded = (bonded /  (372622890-73500000)) * 100

		statmessage = (f'🟩Latest block:\n{int(latestblock):,.0f}\n\n'
						f'🔎Active validators:\n{activevalidators}\n\n'
						# f'Jailed Validators: {', '.join(validatorjailed)}\n'
						f'🔒Bonded:\n{bonded:,.2f}\n'
						f'🔗Percentage bonded:\n{percentage_bonded:,.2f}%\n'
						f'🔐Unbonding:\n{unbonding:,.2f}\n'
						)
		bot.reply_to(message, statmessage)

#CoinGecko API price data
@bot.message_handler(commands=['price'])
def coingecko_price(message):
	coingecko = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcanna'
	try:
		responsecoingecko = requests.get(coingecko,headers={'Accept': 'application/json'},)
	except requests.exceptions.RequestException:
		bot.reply_to(message,'Connection error, the API is currently not working. Please try again later.')
	else:
		coingeckodata = responsecoingecko.json()

		price = coingeckodata[0]['current_price']
		pricechange = coingeckodata[0]['price_change_percentage_24h']
		total_volume = coingeckodata[0]['total_volume']
		high_24h = coingeckodata[0]['high_24h']
		low_24h = coingeckodata[0]['low_24h']

		pricemessage = (f'💲*Price:*\n {price}$ ({pricechange}%)\n\n'
					f'💰*Total Volume:*\n {total_volume:,}$\n\n'
					f'⬆*High 24h:*\n {high_24h}$\n'
					f'⬇*Low 24h:*\n {low_24h}$'
					'\n\n'
					'_Powered by CoinGecko_🦎')
		bot.reply_to(message, pricemessage,parse_mode='Markdown')

#Get the current Staking APR
@bot.message_handler(commands=['stakingapr'])
def staking_apr(message):
	apr_endpoint = 'https://graphql.bitcanna.io/api/rest/price/apr'
	try:
		responseapr = requests.get(apr_endpoint,headers={'Accept': 'application/json'},)
	except requests.exceptions.RequestException:
		bot.reply_to(message,'Connection error, the API is currently not working. Please try again later.')
	else:
		aprdata = responseapr.json()
		apr = float(aprdata['cmc_supply_apr'][0]['apr'])

		aprmessage = (f'The current Staking APR is: \n?? *{apr:,.1f}%*')
		bot.reply_to(message, aprmessage, parse_mode='Markdown')

#Suggest a random validator
@bot.message_handler(commands=['pickvalidator'])
def random_validator(message):
	baseurl = 'http://seed1.bitcanna.io:1317/'
	validatorsurl = baseurl+'/cosmos/staking/v1beta1/validators'
	try:
		responseval = requests.get(validatorsurl,headers={'Accept': 'application/json'},)

	except requests.exceptions.RequestException:
		bot.reply_to(message,'Connection error, the API is currently not working. Please try again later.')
	else:
		datavalidators = responseval.json()
		validators = datavalidators['validators']
		validatornamelist = []

		for validator in validators:
			validator_moniker = validator['description']['moniker']
			validator_address = validator['operator_address']
			validator_name = f'[{validator_moniker}](https://cosmos-explorer.bitcanna.io/validators/{validator_address})'
			validatornamelist.append(validator_name)

	validatormessage = (f'Picking a random validator...🎲\n\n You should delegate to {random.choice(validatornamelist)}')
	bot.reply_to(message, validatormessage,parse_mode='Markdown',disable_web_page_preview=True)

#Subscribe to balance check
@bot.message_handler(commands=['subscribe'])
def subscribe(message):
	chat_type = message.chat.type  # Obtener el tipo de chat del mensaje

    # Verificar si el mensaje proviene de un chat privado
	if chat_type == "private":	
		try:
			chat_id = message.chat.id
			bot.send_message(chat_id, "Let's try to get the initial balance...")
			_, address = message.text.split(maxsplit=1)
			success, response = get_balance(address)
			if success:
				bot.send_message(chat_id, f"Balance of {address}: {response}")
				store_subscription(chat_id, address, response)
				bot.send_message(chat_id, f"You have successfully subscribed to {address}")
			else:
				bot.send_message(chat_id,f"Error with {address}: {response}")

		except ValueError:
			bot.reply_to(message, "Please use the correct format: /subscribe [address] \nExample: /subscribe bcna19gta62js3h3p6s4xdtyyrt7g2zysp5rn0hxnvc ")
	else:
		bot.send_message(chat_id, "This command is only available in private chats.")
		pass

#UnSubscribe to balance check
@bot.message_handler(commands=['unsubscribe'])
def handle_unsubscribe(message):
	chat_type = message.chat.type  # Obtener el tipo de chat del mensaje

    # Verificar si el mensaje proviene de un chat privado
	if chat_type == "private":
		try:
			chat_id = message.chat.id
			_, address = message.text.split(maxsplit=1)
			if unsubscribe(chat_id, address):
				response = f"You have unsubscribed from {address}."
			else:
				response = f"You were not subscribed to {address}, or an error has happened."
		except ValueError:
			response = "Please use the correct format: /unsubscribe [address]"
		bot.send_message(chat_id, response)
	else:
		bot.send_message(chat_id, "This command is only available in private chats.")
		pass
#Balance check
@bot.message_handler(commands=['mybalance'])
def mybalance(message):
	chat_id = message.chat.id
	chat_type = message.chat.type  # Obtener el tipo de chat del mensaje

    # Verificar si el mensaje proviene de un chat privado
	if chat_type == "private":
		addresses = get_addresses(chat_id)
		responses = []
		
		if addresses:
			for address in addresses:
				success, response = get_balance(address)
				if success:
					responses.append(f"Balance of {address}: {response} BCNA")
				else:
					responses.append(f"Error with {address}: {response}")
			final_response = "\n".join(responses)
		else:
			final_response = "You have no subscribed addresses."
		
		bot.send_message(chat_id, final_response)
	else:
		bot.send_message(chat_id, "This command is only available in private chats.")
		pass

#Show subscriptions
@bot.message_handler(commands=['subscriptions'])
def show_subscriptions(message):
    chat_id = message.chat.id
    chat_type = message.chat.type  # Obtener el tipo de chat del mensaje

    # Verificar si el mensaje proviene de un chat privado
    if chat_type == "private":
        subscriptions = get_subscriptions(chat_id)
        if subscriptions:
            response = "Your subscription(s):\n" + "\n".join([address for (address,) in subscriptions])
        else:
            response = "You do not have a subscription."
        bot.send_message(chat_id, response)
    else:
        bot.send_message(chat_id, "This command is only available in private chats.")
        pass


def store_subscription(chat_id, address, balance):
    conn = sqlite3.connect(PATH+DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subscriptions (chat_id, address, balance) VALUES (?, ?, ?)", (chat_id, address, balance))
    conn.commit()
    conn.close()

def unsubscribe(chat_id, address):
    conn = sqlite3.connect(PATH+DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE chat_id=? AND address=?", (chat_id, address))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0  # Retorna True si se realizó alguna eliminación

def get_subscriptions(chat_id):
    conn = sqlite3.connect(PATH+DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT address FROM subscriptions WHERE chat_id=?", (chat_id,))
    subscriptions = cursor.fetchall()  # Obtiene todas las filas que coinciden con la consulta
    conn.close()
    return subscriptions

def get_addresses(chat_id):
    conn = sqlite3.connect(PATH+DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT address FROM subscriptions WHERE chat_id=?", (chat_id,))
    addresses = cursor.fetchall()  # Obtiene todas las filas que coinciden con la consulta
    conn.close()
    return [address[0] for address in addresses]  # Retorna una lista de direcciones

def get_balance(address):
    url = f"https://lcd.bitcanna.io/cosmos/bank/v1beta1/balances/{address}/by_denom?denom=ubcna"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Verificar si la respuesta es válida
            if 'balance' in data and 'amount' in data['balance']:
                balance = int(data['balance']['amount'])
                balance_in_bcna = int(balance) / 1e6
                return True, f"{balance_in_bcna}"
            elif 'code' in data:  # Check the returned code. TODO: error 5 and error 3
                error_message = data.get('message', 'Unknow error. Maybe address is not a valid bech32 address')
                return False, f"Error: {error_message}"
            else:
                return False, "Balance could not be obtained."
        else:
            return False, f"Error when making API request: HTTP State {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Error when making API request: {str(e)}"

def fetch_and_notify():
    while True:
        conn = sqlite3.connect(PATH+DATABASE)
        cursor = conn.cursor()
        # Selecciona la dirección y el balance almacenado para cada suscripción
        cursor.execute("SELECT chat_id, address, balance FROM subscriptions")
        subscriptions = cursor.fetchall()

        for chat_id, address, stored_balance in subscriptions:
            success, new_balance = get_balance(address)
            if success:
                if str(stored_balance) != str(new_balance):
                    #debug: 
					# print(f"Old: {stored_balance}, New: {new_balance}")
                    # Notificar al usuario sobre el cambio de balance
                    bot.send_message(chat_id, f"The balance of {address} has changed: {new_balance} BCNA")
                    # Actualizar el balance almacenado en la base de datos
                    cursor.execute("UPDATE subscriptions SET balance=? WHERE address=? AND chat_id=?", (new_balance, address, chat_id))
                    conn.commit()
            else:
                print(f"It was not possible to obtain the balance for {address}: {new_balance}")

        conn.close()
        time.sleep(180)

# Start a new separated thread
Thread(target=fetch_and_notify).start()

bot.infinity_polling()