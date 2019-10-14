from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
import omdb

engine = create_engine("postgres://dzigpqzoyzzhfq:c379ba3827c9d99b15caac323f3d2e17a695e835b93a8fac174b7de9d8c15bd0@ec2-54-225-106-93.compute-1.amazonaws.com:5432/des33f58ules9j")
db = scoped_session(sessionmaker(bind = engine))
movies_path = os.path.join("res/movies.csv")
omdb.set_default('apikey', '47219f3d')  

movie_file = open(movies_path, "r")

movies_array = movie_file.readlines()

tags = movies_array[0]
del movies_array[0] 

movies_array = sorted(movies_array)
counter = 0
for i in movies_array:

    i = i.strip("\n").split(";")
    title = i[0] # original title for OMDB
    i[1] = int(i[1])
    i[2] = int(i[2])
    res = omdb.imdbid(i[3])
    print(title + " " + str(i[1]))
    db.execute("INSERT INTO movies (title, year, runtime, imdb_id, imdb_rating, description, director, actors, writer, language, genre,\
            country, rated, poster, reviews) VALUES (:title, :year, :runtime, :imdb_id, :imdb_rating, :description, :director, :actors, :writer,\
            :language, :genre, :country, :rated, :poster, :reviews)", {"title": i[0], "year": i[1], "runtime": i[2], "imdb_id": i[3], "imdb_rating": i[4], \
            "description": res["plot"], "director": res["director"], "actors": res["actors"],"writer": res["writer"], "language": res["language"], "genre": res["genre"], \
            "country": res["country"], "rated": res["rated"], "poster": res["poster"], "reviews": ""})

db.commit()
# since database is already full, we no longer need to commit


