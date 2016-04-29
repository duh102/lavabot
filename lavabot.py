import discord, asyncio, re, random, json
import db
from discord.ext import commands
from subprocess import Popen, STDOUT, PIPE

commandRE = re.compile(r'^.quote( (?P<command>[0-9]+|add|search)( (?P<rest>.+))?)?', re.DOTALL)
cowRE = re.compile(r'^.cowsay (?P<rest>.+)', re.DOTALL)
wildcardRE = re.compile(r'(?P<pre>^|[^\\])\*')
quotedRE = re.compile(r'^"(?P<cont>.*)"$')

def quote_format(inString):
  return '[q]: {}'.format(inString)

def searchHelper(inString):
  temp = inString
  quotMat = quotedRE.match(temp)
  if '*' in temp:
    for mat in wildcardRE.finditer(inString):
      temp = wildcardRE.sub('{}%'.format(mat.group('pre')), temp, count=1)
  elif quotMat is not None:
    temp = quotMat.group('cont')
  else:
    temp = '%{}%'.format(temp)
  return temp

description = '''A bot that provides quotes'''
bot = commands.Bot(command_prefix='.', description=description)

@asyncio.coroutine
def quote(select: int=None):
  quoteID = None
  try:
    quoteID = int(select)
  except:
    pass
  quote = "Error; unable to retrieve quote"
  with db.giveSession() as session:
    sel = session.query(db.Quote)
    if quoteID is None:
      numQuotes = int(sel.count())
      quote = str(sel.offset(random.randrange(numQuotes)).first())
    else:
      try:
        quote = str(sel.filter(db.Quote.id == quoteID).one())
      except:
        quote = "No quote with id {}".format(quoteID)
  yield from bot.say(quote_format(quote))

quote_group = bot.group(invoke_without_command=True)(quote)

@quote_group.command(pass_context=True)
@asyncio.coroutine
def add(ctx):
  message = ctx.message
  rest = None
  try:
    rest = commandRE.match(message.clean_content).group('rest')
  except:
    pass
  channel = None
  server = None
  try:
    channel = message.channel.name
    server = message.channel.server.name
  except:
    pass
  newQuote = db.Quote.make_quote(message.author.name, rest, inChannel = channel, inServer = server)
  response = "Error; unable to add quote"
  with db.giveSession() as session:
    session.add(newQuote)
    session.flush()
    response = "Added quote {}".format(newQuote.id)
  yield from bot.say(quote_format(response))

@quote_group.command()
@asyncio.coroutine
def search(*srch: str):
  search = ' '.join(srch)
  if len(search) < 3:
    response = "Error; search string '{}' too short".format(search)
  else:
    response = "Error; unable to search"
    with db.giveSession() as session:
      quotes = session.query(db.Quote).filter(db.Quote.quote.like(searchHelper(search)))
      response = ', '.join([str(quote.id) for quote in quotes])
  yield from bot.say(quote_format(response))

@bot.command(pass_context=True)
@asyncio.coroutine
def cowsay(ctx):
    message = ctx.message
    inputs = ''
    try:
        inputs = cowRE.match(message.clean_content).group('rest')
    except:
        pass
    response = "Error; error running cowsay"
    if len(inputs) > 10:
        proc = Popen(['cowsay', '-n'], stdin=PIPE, stdout=PIPE)
        stdo, stder = proc.communicate(bytes(inputs, 'utf=8'))
        stdout = str(stdo.decode())
        if len(stdout) > 0:
            response = '```{}```'.format(stdout)
    else:
        response = "Error; input too short, must be longer than 10 characters"
    yield from bot.say(response)


@bot.event
@asyncio.coroutine
def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

config = None
with open('config.json', 'r') as configFile:
    config = json.load(configFile)

try:
    db.connectEngine()
    bot.run(config['email'], config['password'])
finally:
    db.disconnectEngine()
