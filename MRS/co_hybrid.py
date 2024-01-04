import pandas as pd
import numpy as np

from ast import literal_eval

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity

from surprise import Reader, Dataset, SVD
from surprise.model_selection import cross_validate

import warnings; warnings.simplefilter('ignore')

md = pd.read_csv('./csvfiles/movies_metadata.csv', encoding='utf-8')

md['genres'] = md['genres'].fillna('[]').apply(literal_eval).apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])
md['year'] = pd.to_datetime(md['release_date'], errors='coerce').apply(lambda x: str(x).split('-')[0] if x != np.nan else np.nan)

C = md['vote_average'].mean()
m = md['vote_count'].quantile(0.95)

qualified = md[(md['vote_count'] >= m) & (md['vote_count'].notnull()) & (md['vote_average'].notnull())]


def weighted_rating(x):
    v = x['vote_count']
    R = x['vote_average']
    return (v/(v+m) * R) + (m/(m+v) * C)


qualified = qualified[['title','overview', 'year', 'vote_count', 'vote_average', 'popularity', 'genres']]
qualified['score'] = qualified.apply(weighted_rating, axis=1)
qualified = qualified.sort_values('score', ascending=False)

tm = qualified.head(100)
tm.to_csv('./csvfiles/toprated.csv', index=False)

links = pd.read_csv('./csvfiles/links_small.csv')
links = links[links['tmdbId'].notnull()]['tmdbId'].astype('int')

md = md.drop([19730, 29503, 35587])
md['id'] = md['id'].astype('int')

def get_recommendations(title):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:100]
    movie_indices = [i[0] for i in sim_scores]
    movies = titles.iloc[movie_indices]
    return movies


credits = pd.read_csv('./csvfiles/credits.csv')
keywords = pd.read_csv('./csvfiles/keywords.csv')
keywords['id'] = keywords['id'].astype('int')
credits['id'] = credits['id'].astype('int')
md = md.merge(credits, on='id')
md = md.merge(keywords, on='id')
smd1 = md[md['id'].isin(links)]

features = ['cast', 'crew', 'keywords']
for feature in features:
    smd1[feature] = smd1[feature].apply(literal_eval)


def get_director(x):
    for i in x:
        if i['job'] == 'Director':
            return i['name']
    return np.nan


smd1['director'] = smd1['crew'].apply(get_director)


def get_list(x):
    if isinstance(x, list):
        names = [i['name'] for i in x]

        if len(names) > 3:
            names = names[:3]
        return names
    return []


features = ['cast', 'keywords']

for feature in features:
    smd1[feature] = smd1[feature].apply(get_list)


def clean_data(x):
    if isinstance(x, list):
        return [str.lower(i.replace(" ", "")) for i in x]
    else:
        if isinstance(x, str):
            return str.lower(x.replace(" ", ""))
        else:
            return ''

#Content-Based Filtering:
features = ['cast', 'keywords', 'director', 'genres']

for feature in features:
    smd1[feature] = smd1[feature].apply(clean_data)
smd1['director'] = smd1['director'].apply(lambda x: [x,x, x])

def create_soup(x):
    return ' '.join(x['keywords']) + ' ' + ' '.join(x['cast'])  + ' '.join(x['director']) + ' '.join(x['genres'])


smd1['soup'] = smd1.apply(create_soup, axis=1)


#CountVectorizer and Cosine Similarity for Content-Based Filtering
#The CountVectorizer is used to convert the text data into a matrix of token counts.
count = CountVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0.0, stop_words='english')
count_matrix = count.fit_transform(smd1['soup'])

#Cosine similarity is calculated based on the count matrix to measure the similarity between movies.
cosine_sim = cosine_similarity(count_matrix, count_matrix)

smd1 = smd1.reset_index()
titles = smd1['title']
indices = pd.Series(smd1.index, index=smd1['title'])


#The collaborative filtering part uses the Surprise library to perform collaborative filtering 
# with the Singular Value Decomposition (SVD) algorithm.

#Use Surprise library to load ratings data and create a dataset.
reader = Reader()
ratings = pd.read_csv('./csvfiles/ratings_small.csv')


#Train the SVD model and perform cross-validation.
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
svd = SVD()
cross_validate(svd, data, measures=['RMSE', 'MAE'])

#Hybrid recommendation
#The convert_int function is defined to convert values to integers, handling potential errors.
def convert_int(x):
    try:
        return int(x)
    except:
        return np.nan


id_map = pd.read_csv('./csvfiles/links_small.csv')[['movieId', 'tmdbId']]
id_map['tmdbId'] = id_map['tmdbId'].apply(convert_int)
id_map.columns = ['movieId', 'id']
id_map = id_map.merge(smd1[['title', 'id']], on='id').set_index('title')

indices_map = id_map.set_index('id')


def hybrid(title ,userId=16):
    idx = indices[title]

    sim_scores = list(enumerate(cosine_sim[int(idx)]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[0:55]
    movie_indices = [i[0] for i in sim_scores]
    movies = smd1.iloc[movie_indices][['title','vote_count', 'vote_average', 'year', 'genres', 'id','overview']]
    movies['est'] = movies['id'].apply(lambda x: svd.predict(userId, indices_map.loc[x]['movieId']).est)
    movies['hybrid_score'] = 0.8 * movies['est'] + (1 - 0.8) * movies['vote_average']
    movies = movies.sort_values('hybrid_score', ascending=False)

    return movies

















