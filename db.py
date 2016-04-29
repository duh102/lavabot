from datetime import datetime
from dateutil.tz import tzlocal, tzutc
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

_engineConn = None
_timefmt = '%Y-%m-%d %H:%M:%S (%Z)'
def connectEngine():
    global _engineConn
    if _engineConn is not None:
        raise Exception("Engine already connected")
    _engineConn = create_engine('sqlite:///quotes.db')

def disconnectEngine():
    global _engineConn
    if _engineConn is None:
        raise Exception("Engine already disconnected")
    _engineConn = None

@contextmanager
def giveEngine():
    global _engineConn
    if _engineConn is None:
        raise Exception('Engine not connected')
    try:
        yield _engineConn
    except:
        _engineConn.dispose()

@contextmanager
def giveSession():
    global _engineConn
    if _engineConn is None:
        raise Exception('Engine not connected')
    Session = sessionmaker(_engineConn)
    session = Session()
    try:
        yield session
    except:
        session.rollback()
    finally:
        session.commit()

def giveNowUTC():
    return datetime.now(tzlocal()).astimezone(tzutc())

Base = declarative_base()

class Quote(Base):
    __tablename__ = 'quote'
    id = Column(Integer, primary_key=True)
    submitter = Column(String(64), index=True)
    channel = Column(String(64), index=True)
    server = Column(String(64), index=True)
    submit_timestamp = Column(DateTime, default=giveNowUTC, index=True, nullable=False)
    quote = Column(String(512), nullable=False)

    @classmethod
    def make_quote(cls, inSubmit, inQuote, inChannel=None, inServer=None):
        return cls(submitter=inSubmit, quote=inQuote, channel=inChannel, server=inServer)

    def tsAsUTC(self):
        return self.submit_timestamp.replace(microsecond=0, tzinfo=tzutc())

    def __str__(self):
        return '#{} [{}] by {}\n{}'.format(str(self.id), self.tsAsUTC().strftime(_timefmt), self.submitter or '<nobody>', self.quote)

connectEngine()
with giveEngine() as engine:
    Base.metadata.create_all(engine)
disconnectEngine()
