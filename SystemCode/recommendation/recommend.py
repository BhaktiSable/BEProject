# Initialize Library Setup

import pandas as pd
import numpy as np
import re
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity

# Check & Query
filename = r'C:\Users\nehab\Desktop\Be project\BEProject\SystemCode\instance\mydb.db'
table_name = 'course'
sqlite_conn = sqlite3.connect(filename)

# Query Table
rawdata = pd.read_sql('SELECT * FROM ' + table_name, sqlite_conn, index_col='courseID')
sqlite_conn.close()

# Utility functions for recommendation module
# 1) Text Preprocessing
# Initilization
stopwordsdic = stopwords.words('english')
lemmatizer = WordNetLemmatizer()


# Takes any rawtext as input and apply text preprocessing:
#   - remove all non-ASCII characters
#   - lower-casing all text and remove unecessary spaces
#   - remove punctuations
#   - remove stopwords
#   - lemmatize words
#   - create bag-of-words (bow) strings
def text_preprocess(rawtext):
    text = re.sub('([^\x00-\x7F])+', '', rawtext)  # Remove all non ASCII characters
    text = text.lower()  # lower casing all words
    text = text.strip()  # Remove White Spaces
    text = re.sub('[^A-Za-z0-9]+', ' ', text)  # Remove Punctuations
    text = word_tokenize(text)  # Tokenize
    text = [word for word in text if word not in stopwordsdic]  # Remove stopwords
    text = [lemmatizer.lemmatize(word) for word in text]  # Lemmatize words
    bow = ' '.join(text)  # Create Bag-of-Words
    return bow


# 2) Encoding User Input Features:
# Takes list of categorical data (course difficulty, course duration and course free option) as input
# Returns one-hot encoded features.
def categorical_encode(categorical_input):
    encode = np.zeros((1, 6))
    # Binary Encode Course Duration (0 - No Preference, 1 - Short, 2 - Medium, 3 - Long)
    if categorical_input[0] > 0:
        encode[0, categorical_input[0] - 1] = 1
    # Binary Encode Course Difficulty (0 - No Preference, 1 - Introductory, 2 - Intermediate, 3 - Advanced)
    if categorical_input[1] > 0:
        encode[0, categorical_input[1] + 2] = 1
    return encode


# 3) TfIdf Vectorizer:
# Takes list of tokens as input and apply TfIdf Vectorization based on the pretrained dictionary.
def tfidf_vectorize(text, vectorizer):
    # Load Tfidf Vectorizer
    # vectorizer_file = open(config.tfidf_vectorizer_filepath, 'rb')
    # vectorizer = pickle.load(vectorizer_file)
    # vectorizer_file.close()
    tfidf = vectorizer.transform([text])
    return tfidf


# 4) Cosine Similarity:
# Takes 2 vectors and calculate cosine similarity
def cond_sim(input_vec, data_vec):
    input_durr = input_vec[:, :3]
    input_diff = input_vec[:, 3:]
    data_durr = data_vec[:, :3]
    data_diff = data_vec[:, 3:6]
    # print(str(input_durr)+ " diff "+str(input_diff)+" data dur"+str(data_durr)+" "+str(data_diff))
    # print('inp vect '+ str(input_vec)+ 'len '+str((input_vec.shape)))
    # print('data vect '+ str(data_vec)+ 'len '+str((data_vec.shape)))
    if (input_diff.sum() + input_durr.sum()) == 0:
        sim = np.ones(data_vec.shape[0])
    elif input_durr.sum() == 0:
        sim = cosine_similarity(input_diff, data_diff)
    elif input_diff.sum() == 0:
        sim = cosine_similarity(input_durr, data_durr)
    else:
        data_vec=data_vec[:,:6]
        sim = cosine_similarity(input_vec, data_vec)
    return sim


# 5) Ranking based on popularity index
# Given a sorted and threshold filtered ID of recommendations
# Batch rank for every batch_size of ID by rating.
def ranking(mask, text_sim, categorical_sim, rating):
    target_idx = np.arange(text_sim.shape[0])[mask]
    target_text_sim = text_sim[mask]
    target_categorical_sim = categorical_sim[mask]
    target_rating = rating[mask]
    target_scores = sorted(np.unique(target_categorical_sim), reverse=True)
    rec_idx = np.array([], dtype=int)
    rec_sim = np.array([])
    for score in target_scores:
        group_mask = (target_categorical_sim == score)
        group_idx = target_idx[group_mask]
        group_text_sim = target_text_sim[group_mask]
        group_rating = target_rating[group_mask]
        group_sort_idx = np.argsort(group_rating)[::-1]
        rec_idx = np.append(rec_idx, group_idx[group_sort_idx])
        rec_sim = np.append(rec_sim, group_text_sim[group_sort_idx])
    return rec_sim, rec_idx


# 6) Load-up Pickle Object Data Files
def load_pickle(filename):
    data_file = open(filename, 'rb')
    data = pickle.load(data_file)
    data_file.close()
    return data


# CONFIGURATION FOR RECOMMENDER MODULE
# DATA FILE PATH
tfidf_data_filepath = (r'C:\Users\nehab\Desktop\Be project\BEProject\SystemCode\recommendation\FeatureMap\tfidf_data.pickle')
categorical_data_filepath = r'C:\Users\nehab\Desktop\Be project\BEProject\SystemCode\recommendation\FeatureMap\categorical_data.pickle'
tfidf_vectorizer_filepath = r'C:\Users\nehab\Desktop\Be project\BEProject\SystemCode\recommendation\FeatureMap\tfidf_vectorizer.pickle'
# TEXT BASED RECOMMENDATION THRESHOLD
text_thres = 0.5
# MINIMUM FREE COURSE COUNT THRESHOLD
free_show_thres = 2
# RECOMMENDATION RESULTS SIZE
recommend_topn = 50
# DEFAULT POPULAR RESULTS SIZE
recommend_default_topn = 10
#multiplier=5


# Recommendation module
# Takes user input and returns a sorted list of recommended courses.

# Initialize Library Setup





# Recommend Function
def recommend(user_input, rating_data, tfidf_vectorizer, tfidf_data, categorical_data):
    # 1. Feature Extraction - Text Based (TfIdf)
    # Load Tfidf Data Sparse Matrix
    # tfidf_data_file = open(config.tfidf_data_filepath, 'rb')
    # tfidf_data = pickle.load(tfidf_data_file)
    # tfidf_data_file.close()
    # Text Input and Similarity Score
    text_input = user_input[0]
    #print('text input:  ',text_input)
    text_processed = text_preprocess(text_input)
    tfidf_vect = tfidf_vectorize(text_processed, tfidf_vectorizer)
    tfidf_sim = cosine_similarity(tfidf_vect, tfidf_data).ravel()

    # 2. Feature Extraction - Categorical Based (One-Hot Encoded)
    # Load Categorical One-Hot Encoded Sparse Matrix

    # categorical_data_file = open(config.categorical_data_filepath, 'rb')
    # categorical_data = pickle.load(categorical_data_file)
    # categorical_data_file.close()
    # Categroical Input and Similarity Score
    categorical_input = user_input[1:3]
    #print('cipt: ',categorical_input)
    categorical_vect =categorical_encode(categorical_input)

    categorical_sim = cond_sim(categorical_vect, categorical_data[:, :-1]).ravel()

    # 3. Recommendation Masks (Free vs Paid Courses Masks)
    free_option_ind = user_input[-1]
    free_option_data = categorical_data[:, -1]
    thres_mask = (tfidf_sim > text_thres)
    if free_option_ind == 1:
        free_mask = ((free_option_data == 1) * thres_mask) == 1
    else:
        free_mask = (np.ones(tfidf_data.shape[0]) * thres_mask) == 1
    paid_mask = ((np.ones(tfidf_data.shape[0]) * thres_mask) - free_mask) == 1

    # 4. Apply Masks and Rank by categorical_sim group and rating
    rec_sim, rec_idx = ranking(free_mask, tfidf_sim, categorical_sim, rating_data)

    # 5. Append paid courses if number of free courses below a threshold
    if (free_mask.sum() < free_show_thres) and (paid_mask.sum() > 0):
        paid_sim, paid_idx = ranking(paid_mask, tfidf_sim, categorical_sim, rating_data)
        rec_sim = np.append(rec_sim, paid_sim)
        rec_idx = np.append(rec_idx, paid_idx)
    # 6. Convert Index to courseID
    rec_idx = rec_idx + 1
    course_sim = rec_sim[:recommend_topn].tolist()
    course_idx = rec_idx[:recommend_topn].tolist()

    return course_idx


def recommend_default(rating_data):
    sort_idx = (np.argsort(rating_data)[::-1])
    sort_course = sort_idx[:recommend_default_topn]
    default_course = [int(x+1) for x in sort_course]
    return default_course


'''ainput = ['data structures', 1, 0, 1]
rawdata_rating = rawdata['popularity_index']
a=load_pickle(tfidf_data_filepath)
b=load_pickle(categorical_data_filepath)
c=load_pickle(tfidf_vectorizer_filepath)
idx=recommend(ainput,rawdata_rating,c,a,b)
for i in idx:
    print(rawdata['title'][i])'''


# ainput = ['machine learning', 1, 0, 1]  # what to learn, difficulty,duration.free
# idx=recommend(ainput,rawdata_rating,c,a,b)

# for i in idx:
#     print(rawdata['title'][i])


# ainput = ['web development', 0, 1, 1]  # what to learn, difficulty,duration.free
# idx=recommend(ainput,rawdata_rating,c,a,b)

# for i in idx:
#     print(rawdata['title'][i])

# ainput = ['data science', 0, 2, 1]  # what to learn, duration,difficulty,.free
# idx=recommend(ainput,rawdata_rating,c,a,b)

# for i in idx:
#     print(rawdata['title'][i])

'''ainput = ['web development', 2, 1, 0]  # what to learn, difficulty,duration.free
idx=recommend(ainput,rawdata_rating,c,a,b)

for i in idx:
    print(rawdata['title'][i])'''

# ainput = ['cloud computing', 2, 3, 0]  # what to learn, difficulty,duration.free
# idx=recommend(ainput,rawdata_rating,c,a,b)

# for i in idx:
#     print(rawdata['title'][i])
