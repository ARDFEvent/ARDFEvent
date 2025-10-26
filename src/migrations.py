import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session


def migrate(dbstr):
    db = sqlalchemy.create_engine(dbstr)

    sess = Session(db)

    try:
        sess.execute(text("ALTER TABLE runners ADD COLUMN startno INT;"))
        print("Migrated startno:", dbstr)
    except:
        pass

    sess.commit()
    sess.close()
