from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Category, Item, User

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

user1 = User(name='Buzz Lightyear',
             email='ToInfinityAndBeyond@StarCommand.com',
             picture="""
                http://vignette2.wikia.nocookie.net/parody/images/5/54/Buzz_toy_story_3.png
                """)

session.add(user1)
session.commit()

user2 = User(name='Woody',
             email='TheresASnakeInMyBoot@AnysFavorite.com',
             picture='https://preview.ibb.co/jpBbRF/woody.jpg')

session.add(user2)
session.commit()

user3 = User(name='Rex',
             email="Rex@ToyStory.com",
             picture='https://image.ibb.co/ejSN0a/Rex_1.png')

session.add(user3)
session.commit()

category1 = Category(user_id=1,
                     name='Toy Story Items')

session.add(category1)
session.commit()

category2 = Category(user_id=2,
                     name='Toy Story Characters')

session.add(category2)
session.commit()

item1 = Item(user_id=1,
             name='Infinity Blaster',
             description="""
                 The Buzz Lightyear Infinity Blaster
                 is used to stop the evil emperor Zurg,
                 who is threatening the Galactic Alliance.
                 """,
             category=category1)

session.add(item1)
session.commit()

item2 = Item(user_id=2,
             name='Cowboy Hat',
             description='The official hat to worn by Woody!',
             category=category1)

session.add(item2)
session.commit()

item3 = Item(user_id=1,
             name='Buzz Lightyear',
             description="""
                In Toy Story, he begins the series believing he is
                a real space ranger and develops a rivalry with
                Woody, who resents him for getting more attention
                as the newcomer.
                """,
             category=category2)

session.add(item3)
session.commit()

item4 = Item(user_id=3,
             name='Rex the T-Rex',
             description="""
                Rex is an excitable large, green, plastic Tyrannosaurus
                rex and suffers from anxiety, an inferiority complex and
                the concern that he is not scary enough.
                """,
             category=category2)

session.add(item4)
session.commit()

print "added categories and items!"
