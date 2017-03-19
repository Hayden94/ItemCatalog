from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

category1 =Category(name='Sports')

session.add(category1)
session.commit()

item1 = Item(name='Snowboard', description='These are used to shred gnar on snow.', category=category1)

session.add(item1)
session.commit()

item2 = Item(name='Skateboard', description='These are used to shred gnar on concrete.', category=category1)

session.add(item2)
session.commit()

print "added categories and items!"
