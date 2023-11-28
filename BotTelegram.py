import telebot
import requests
import random
import datetime
from mytoken import token


bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, 'Howdy, how are you doing?')

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
			validator_address = validator['operator_address']
			
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

bot.infinity_polling()