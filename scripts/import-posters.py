"""Join public poster metadata to MovieLens links by IMDb ID (requires pyarrow)."""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
import pyarrow.parquet as pq

archive, metadata = sys.argv[1:3]
posters = {int(row['imdbId'][2:]): row['poster'] for row in pq.read_table(metadata).to_pylist()
           if row['imdbId'].startswith('tt') and row['imdbId'][2:].isdigit()
           and row['poster'].startswith('https://m.media-amazon.com/images/')}
if len(sys.argv) >= 5:
    with open(sys.argv[3]) as f:
        classic_ids = {r['movie_id']: int(r['imdbId']) for r in csv.DictReader(f) if r['imdbId'].isdigit()}
    with open(sys.argv[4]) as f:
        for movie_id, url in csv.reader(f):
            if movie_id in classic_ids and url.startswith('https://m.media-amazon.com/images/'):
                posters[classic_ids[movie_id]] = url.replace('..jpg', '._V1_SX300.jpg')
with zipfile.ZipFile(archive) as z:
    links = csv.DictReader(io.StringIO(z.read('ml-latest-small/links.csv').decode()))
    mapping = {row['movieId']: posters[int(row['imdbId'])] for row in links if int(row['imdbId']) in posters}
catalog = json.loads(Path('frontend/public/data/catalog.json').read_text())
ids = {str(m['id']) for m in catalog['movies']}
mapping = {k: v for k, v in mapping.items() if k in ids}
Path('frontend/src/posters.json').write_text(json.dumps(mapping, indent=2) + '\n')
print(f'Matched {len(mapping)} of {len(ids)} films by IMDb ID.')
