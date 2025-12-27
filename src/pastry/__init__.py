from src.pastry.local_index import LocalIndex, MovieRecord

idx = LocalIndex()
idx.upsert(MovieRecord(movie_id="1", title="A", popularity=10.0, vote_average=7.2, runtime=120))
idx.upsert(MovieRecord(movie_id="2", title="B", popularity=55.0, vote_average=6.9, runtime=95))
idx.upsert(MovieRecord(movie_id="3", title="C", popularity=30.0, vote_average=8.1, runtime=140))

print([r.movie_id for r in idx.top_k("popularity", 2)])         # ['2','3']
print([r.movie_id for r in idx.range_query("vote_average", 7, 9)])  # ['1','3']
