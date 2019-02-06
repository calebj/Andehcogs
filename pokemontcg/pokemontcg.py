#!/usr/bin/env python3
import discord
import asyncio
from functools import lru_cache
from pokemontcgsdk import Card
from pokemontcgsdk import Set
from pokemontcgsdk import Type
from pokemontcgsdk import Supertype
from pokemontcgsdk import Subtype

# The maximum number of lines the bot will post to a public server in one
# message. Anything larger will be private messaged to avoid clutter
MAX_LINES = 15

client = discord.Client()

# Gets the token from a file
def read_token(filename):
	f = open(filename, 'r')
	token = f.read()
	return token

# A help message listing the available commands and syntax
def cardbot_help():
	return """
```
!search [card-name]
    Gives a list of all cards matching the search
    [card-name], as well as the set code and name.
    e.g.
        !search ambipom
        !search ninja boy
        !search splash energy
!show [set-code]
    Displays the text and image of the given card
    from the given set. If you are unsure of the
    set code, find it using !search first.
    e.g.
        !show xy11-91
        !show xy11-103
        !show xy9-113
!text [set-code]
    Similar to !show, however gives just the card text
    in a copy-and-pastable format.
    e.g.
        !text xy11-91
        !text xy11-103
        !text xy9-113
```
	"""

@client.event
@asyncio.coroutine
def on_ready():
	print("Logged in as '%s' (%s)" % (client.user.name, client.user.id))

@client.event
@asyncio.coroutine
def on_message(received):
	message = ""
	recipient = received.channel

	if received.content.startswith("!help"):
		yield from client.send_message(received.author, cardbot_help())

	match = re.match("!search\s+(.*)$", received.content)
	if match:
		(message, results) = cardbot.pokemontcg.search(match.group(1))
		if results > MAX_LINES:
			yield from client.send_message(
				recipient,
				"Results list is too long, messaging instead"
			)
			recipient = received.author

	match = re.match("!show\s+(?:(.*)\s+)?(.*)$", received.content)
	if match:
		message = cardbot.pokemontcg.show(match.group(1), match.group(2))

	match = re.match("!text\s+(?:(.*)\s+)?(.*)$", received.content)
	if match:
		message = cardbot.pokemontcg.text(match.group(1), match.group(2))

	if type(message) == discord.embeds.Embed:
		yield from client.send_message(recipient, embed=message)
	elif type(message) == str and len(message) > 0:
		yield from client.send_message(recipient, message)

def main():
	# Process command-line arguments to get the token
	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-t', '--token', help='The Discord API token')
	group.add_argument('-f', '--token-file',
		help='A file containing the Discord API token')
	args = parser.parse_args()
	if args.token:
		token = args.token
	elif args.token_file:
		token = read_token(args.token_file)
	else:
		print("Please specify a valid API token with -t or -f")
		return

	logging.basicConfig(level=logging.INFO)
	client.run(token)

if __name__ == '__main__':
	main()

# Conversion from type name to emoji
emoji = {
	'Colorless' : '<:ecolorless:362734594593914890>',
	'Darkness'  : '<:edarkness:362733180274606080>',
	'Dragon'    : '<:edragon:362737396179271680>',
	'Fairy'     : '<:efairy:362733851371503616>',
	'Fighting'  : '<:efighting:362732793995984917>',
	'Fire'      : '<:efire:362731242044653578>',
	'Free'      : '<:ecolorless:362734594593914890>',
	'Grass'     : '<:egrass:362730672680599552>',
	'Lightning' : '<:elightning:362731984474079233>',
	'Psychic'   : '<:epsychic:362732305359568908>',
	'Metal'     : '<:emetal:362733507539369984>',
	'Water'     : '<:ewater:362731629988544512>',
}

# Conversion from type name to hex colour
colour = {
	'Colorless' : 0xF5F5DA,
	'Darkness'  : 0x027798,
	'Dragon'    : 0xD1A300,
	'Fairy'     : 0xDD4787,
	'Fighting'  : 0xC24635,
	'Fire'      : 0xD7080C,
	'Grass'     : 0x427B18,
	'Lightning' : 0xF9D029,
	'Psychic'   : 0xB139B6,
	'Metal'     : 0xAFAFAF,
	'Water'     : 0x02B2E6,
}

# Conversion from type name to PokeBeach shorthand
short_energy = {
	'Colorless' : "[C]",
	'Darkness'  : "[D]",
	'Fairy'     : "[Y]",
	'Fighting'  : "[F]",
	'Fire'      : "[R]",
	'Free'      : "[ ]",
	'Grass'     : "[G]",
	'Lightning' : "[L]",
	'Psychic'   : "[P]",
	'Metal'     : "[M]",
	'Water'     : "[W]",
}

# Given a string, searches for cards by name using the given string. Return a
# list of matches sorted by release, and the set name and code the card was
# released in
def search(name):
	if name == "":
		return ("", 0)

	# Users will often enter 'hydreigon ex' when they really mean
	# 'hydreigon-ex'. This annoying, but simply inserting the dash does not
	# work as it makes Ruby/Sapphire era ex cards unaccessible. Instead,
	# search for both
	cards = []
	if name.lower().endswith(" ex"):
		cards.extend(Card.where(name = name.lower()))
		cards.extend(Card.where(name = name.lower().replace(" ex", "-ex")))
	# GX cards do not have the same issue, so we can simply insert the dash
	# as expected
	elif name.lower().endswith(" gx"):
		cards.extend(Card.where(name = name.lower().replace(" gx", "-gx")))
	# Otherwise, search for the given text
	else:
		cards = Card.where(name = name)

	# Give an error if there are no matches
	if len(cards) == 0:
		return ("No matches for search '%s'" % name, 0)

	# If there is exactly one match, save time for the user and give the
	# !show output instead
	if len(cards) == 1:
		return (show(cards[0].name, cards[0].set_code), 1)

	# If there are matches, build a string with the name, set and set code
	# of every match
	cards_with_sets = []
	for card in cards:
		card_set = Set.find(card.set_code)

		# Re-arrange the release data so it is ISO
		date_split = card_set.release_date.split("/")
		card_set.release_date = ("%s-%s-%s" %
			(date_split[2], date_split[0], date_split[1]))

		cards_with_sets.append((card, card_set))

	# Sort the list of cards by set release date
	cards_with_sets.sort(key = lambda card : card[1].release_date)

	# Create the returned string
	return_str = "Matches for search '%s'\n" % name
	for card in cards_with_sets:
		return_str += ("%s - %s %s/%s (`%s-%s`)\n" %
			(card[0].name, card[1].name, card[0].number,
			 card[1].total_cards, card[1].code, card[0].number))
	return (return_str, len(cards_with_sets))

def embed_create(card, card_set):
	embed = None
	if card.supertype == "Pokémon":
		embed = pokemon_embed(card)
	elif card.supertype == "Trainer" or card.supertype == "Energy":
		embed = trainer_embed(card)

	# Image
	embed.set_image(url=card.image_url)

	# Set and legality
	text = "%s - %s/%s " % (card_set.name, card.number, card_set.total_cards)
	if card_set.standard_legal == True:
		text += " (Standard)"
	elif card_set.expanded_legal == True:
		text += " (Expanded)"
	else:
		text += " (Legacy)"
	embed.set_footer(text=text, icon_url=card_set.symbol_url)

	return embed
	

# Construct an Embed object from a Pokemon card and it's set
def pokemon_embed(card):

	# Name, type(s), HP
	title = card.name
	if card.hp != None:
		title += " - HP%s" % (card.hp)
	title += " - " + " / ".join(list(map(lambda x : emoji[x], card.types)))

	# Subtype, evolution
	desc = "%s Pokémon" % card.subtype
	if card.evolves_from != None and card.evolves_from != "":
		desc += " (Evolves from %s)" % card.evolves_from

	embed = discord.Embed(title=title, color=colour[card.types[0]], description=desc)

	# Ability
	if card.ability != None:
		name = "%s: %s" % (card.ability['type'], card.ability['name'])
		embed.add_field(name=name, value=card.ability['text'] or '\u200b')

	# Attacks
	if card.attacks != None:
		for attack in card.attacks:
			name = ""
			text = ""
			for cost in attack['cost']:
				name += "%s" % emoji[cost]
			name += " %s" % attack['name']
			if attack['damage'] != '':
				name += " - %s" % attack['damage']
			if attack['text'] != None and attack['text'] != "":
				text = attack['text']
			else:
				text = '\u200b'
			embed.add_field(name=name, value=text, inline=False)

	# Weakness, resistance, retreat
	name = ""
	if card.weaknesses != None:
		name += "Weakness: "
		for weakness in card.weaknesses:
			name += ("%s (%s)" %
				(emoji[weakness['type']], weakness['value']))
	if card.resistances != None:
		name += " - Resistance: "
		for resistance in card.resistances:
			name += ("%s (%s)" %
				(emoji[resistance['type']], resistance['value']))
	if card.retreat_cost != None:
		name += " - Retreat: "
		name += "%s" % emoji['Colorless'] * len(card.retreat_cost)
	if name != "":
		embed.add_field(name=name, value='\u200b', inline=False)

	return embed

# Construct an Embed object from a Trainer or Energy card and it's set
def trainer_embed(card):
	embed = discord.Embed(title=card.name, description=card.subtype)
	for text in card.text:
		embed.add_field(name='\u200b', value=text)
	return embed
	
# Get a card object from the passed name and set code
def parse_card(name, card_set):
	# If the card set includes a specific number, we can just use that to
	# get the card
	card = None
	if "-" in card_set:
		card = Card.find(card_set)
		if card == None:
			return "No results for card `%s`" % card_set
	else:
		# Search for the given card
		cards = Card.where(name = name, setCode=card_set)

		if len(cards) == 0:
			return ("No results found for '%s' in set `%s`" %
				(name, card_set))

		if len(cards) > 1:
			return (
"""
Too many results. Try specifying the card number too. For example
`!show %s %s-%s`
""" % (name, card_set, cards[0].number)
			)

		card = cards[0]
	return card

# Given a card name and set code, get an embed for that card
@lru_cache(maxsize=1024)
def show(name, card_set_text):
	card = parse_card(name, card_set_text)
	if type(card) == str:
		return card
	card_set = Set.find(card.set_code)
	return embed_create(card, card_set)

# Given a card name and set code, return the card text as plain text
def text(name, card_set_text):
	card = parse_card(name, card_set_text)
	card_set = Set.find(card.set_code)

	# Create a string for the card text
	return_str = "```\n"

	# Pokemon are the most involved as they have a lot going on
	if card.supertype == "Pokémon":
		# Start with the Pokemon's name and type(s)
		return_str += "%s - %s" % (card.name, "/".join(card.types))

		# Some Pokemon have no HP (e.g. the second half of LEGEND cards),
		# so do only add it if it exists
		if card.hp != None:
			return_str += " - HP%s\n" % (card.hp)
		else:
			return_str += "\n"

		return_str += "%s Pokemon" % card.subtype
		if card.evolves_from != None and card.evolves_from != "":
			return_str += " (Evolves from %s)" % card.evolves_from
		return_str += "\n\n"

		# Add the ability if present
		if card.ability != None:
			return_str += "%s: %s\n" % (card.ability['type'], card.ability['name'])
			return_str += "%s\n" % card.ability['text']
			return_str += "\n"

		# Add any attacks, including shorthand cost, text and damage
		if card.attacks != None:
			for attack in card.attacks:
				for cost in attack['cost']:
					return_str += "%s" % short_energy[cost]
				return_str += " %s" % attack['name']
				if attack['damage'] != '':
					return_str += ": %s damage\n" % attack['damage']
				else:
					return_str += "\n"
				if attack['text'] != None:
					return_str += "%s\n" % attack['text']
				return_str += "\n"

		# Add weakness, resistances and retreat if they exist
		if card.weaknesses != None:
			for weakness in card.weaknesses:
				return_str += ("Weakness: %s (%s)\n" %
					(weakness['type'], weakness['value']))
		if card.resistances != None:
			for resistance in card.resistances:
				return_str += ("Resistance: %s (%s)\n" %
					(resistance['type'], resistance['value']))
		if card.retreat_cost != None:
			return_str += "Retreat: %s" % len(card.retreat_cost)

	# Trainers and Energy are a lot easier
	elif card.supertype == "Trainer" or card.supertype == "Energy":
		return_str += "%s\n" % card.name
		return_str += "%s\n\n" % card.subtype
		return_str += "%s\n" % "\n\n".join(card.text)

	# Finally, get the set and legality info
	return_str += "\n\n%s - %s/%s" % (card_set.name, card.number, card_set.total_cards)
	if card_set.standard_legal == True:
		return_str += " (Standard)"
	elif card_set.expanded_legal == True:
		return_str += " (Expanded)"
	else:
		return_str += " (Legacy)"

	return_str += "```\n"
return return_str()
