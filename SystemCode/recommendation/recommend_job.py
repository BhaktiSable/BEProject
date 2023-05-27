from sklearn.feature_extraction.text import TfidfVectorizer
import csv
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
filename = r'C:\Users\nehab\Desktop\Be project\BEProject-Bhakti\BEProject-Bhakti\SystemCode\instance\mydb.db'
table_name = 'course'
sqlite_conn = sqlite3.connect(filename)

# Query Table
rawdata = pd.read_sql('SELECT * FROM ' + table_name, sqlite_conn, index_col='courseID')
sqlite_conn.close()
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



job_role = {'Data Analyst': ['Statistical analysis','ANOVA','MySQL','SQL','Problem solving','Oracle',
                             'Regression analysis',
                             'Data manipulation',
                             'R',
                             'Seaborn',
                             'Azure',
                             'Power BI',
                             'SciPy',
                             'Matplotlib',
                             'Tableau',
                             'PostgreSQL',
                             'Hypothesis testing',
                             'AWS',
                             'Machine learning',
                             'Pandas',
                             'Data analysis',
                             'Data cleaning',
                             'Google Analytics',
                             'NumPy',
                             'SQL Server',
                             'Communication skills',
                             'Data visualization',
                             'Critical thinking',
                             'Statistics',
                             'Excel',
                             'Time series analysis',
                             'MongoDB',
                             'QlikView',
                             'Python',
                             'Looker'],
            'Data Scientist': ['Statistical analysis',
                               'Hadoop',
                               'SQL',
                               'Deep learning',
                               'Problem solving',
                               'TensorFlow',
                               'NLP',
                               'R',
                               'Azure',
                               'Experimentation',
                               'Model tuning',
                               'Statistical modeling',
                               'Scikit-learn',
                               'Data wrangling',
                               'Machine learning',
                               'AWS',
                               'Big data',
                               'Data analysis',
                               'Reinforcement learning',
                               'PyTorch',
                               'Communication skills',
                               'Data visualization',
                               'Keras',
                               'Spark',
                               'Python'],
            'Software Developer': ['API development',
                                   'Docker',
                                   'Windows',
                                   'Kubernetes',
                                   'MySQL',
                                   'SQL',
                                   'Web development',
                                   'Problem solving',
                                   'Git',
                                   'Oracle',
                                   'DevOps',
                                   'Agile',
                                   'macOS',
                                   'Data structures',
                                   'PHP',
                                   'C#',
                                   'Flask',
                                   'JavaScript',
                                   'React',
                                   'C++',
                                   'Mobile app development',
                                   'Programming',
                                   'Testing',
                                   'Spring',
                                   'Linux',
                                   'Cloud computing',
                                   'Angular',
                                   'Ruby on Rails',
                                   'Debugging',
                                   'PostgreSQL',
                                   'Unit testing',
                                   'Kotlin',
                                   'Swift',
                                   'Objective-C',
                                   'SQL Server',
                                   'Unity',
                                   'Ruby',
                                   '.NET',
                                   'Object-oriented programming (OOP)',
                                   'Node.js',
                                   'MongoDB',
                                   'Java',
                                   'Django',
                                   'Python',
                                   'Algorithms'],
            'Full Stack Developer': ['Semantic UI',
                                     'API development',
                                     'MySQL',
                                     'Git',
                                     'Oracle',
                                     'Agile',
                                     'Ionic',
                                     'Express',
                                     'Vue.js',
                                     'PHP',
                                     'Python',
                                     'JavaScript',
                                     'REST APIs',
                                     'React',
                                     'Database management',
                                     'CSS',
                                     'Materialize',
                                     'Front-end development',
                                     'HTML',
                                     'Angular',
                                     'Ruby on Rails',
                                     'PostgreSQL',
                                     'Bootstrap',
                                     'React Redux',
                                     'SQL Server',
                                     'Back-end development',
                                     'ASP.NET',
                                     'Node.js',
                                     'jQuery',
                                     'Agile methodologies',
                                     'Vue.js Vuex',
                                     'MongoDB',
                                     'Express.js',
                                     'React Native',
                                     'Electron',
                                     'Django',
                                     'Flask'],
            'Web Developer': ['SQL',
                              'Responsive design',
                              'Git',
                              'Agile',
                              'Vue.js',
                              'PHP',
                              'JavaScript',
                              'React',
                              'REST APIs',
                              'CSS',
                              'HTML',
                              'Angular',
                              'Bootstrap',
                              'Web performance optimization',
                              'SEO',
                              'UI/UX design',
                              'Node.js',
                              'jQuery',
                              'Python'],
            'Cloud Solutions Architect': ['Data migration',
                                          'Google Cloud Platform',
                                          'Networking',
                                          'Docker',
                                          'AWS',
                                          'Terraform',
                                          'Kubernetes',
                                          'Azure',
                                          'Security',
                                          'Architecture design',
                                          'Cloud computing'],
            'Cybersecurity Analyst': ['Penetration testing',
                                      'Firewall management',
                                      'Firewalls',
                                      'Nmap',
                                      'Intrusion detection',
                                      'Security analysis',
                                      'SIEM',
                                      'Metasploit',
                                      'Vulnerability scanners',
                                      'Risk assessment',
                                      'Antivirus software',
                                      'IDS/IPS'],
            'Network Administrator': ['Routing protocols',
                                      'Active Directory',
                                      'WAN',
                                      'LAN',
                                      'VPN',
                                      'Windows Server',
                                      'Problem solving',
                                      'Security',
                                      'TCP/IP',
                                      'DHCP',
                                      'DNS',
                                      'Linux',
                                      'Virtualization',
                                      'Juniper',
                                      'Firewalls',
                                      'Cisco'],
            'Network Architect': ['Routing protocols',
                                  'Active Directory',
                                  'WAN',
                                  'LAN',
                                  'VPN',
                                  'Windows Server',
                                  'Problem solving',
                                  'Security',
                                  'TCP/IP',
                                  'DHCP',
                                  'DNS',
                                  'Linux',
                                  'Virtualization',
                                  'Network design',
                                  'Juniper',
                                  'Firewalls',
                                  'Cisco'],
            'Database Administrator': ['Database backup and recovery',
                                       'PostgreSQL',
                                       'MySQL',
                                       'SQL',
                                       'Windows Server',
                                       'Problem solving',
                                       'Oracle',
                                       'Database security',
                                       'MongoDB',
                                       'Database performance tuning',
                                       'Linux',
                                       'Database design',
                                       'Shell scripting'],
            'DevOps Engineer': ['Docker',
                                'Ubuntu',
                                'Proxy Servers',
                                'Kubernetes',
                                'Ansible',
                                'LVM',
                                'Git',
                                'RedHat',
                                'EC2',
                                'SSL/TLS',
                                'Monitoring and logging tools',
                                'Prometheus',
                                'Automation tools',
                                'Azure',
                                'Linux',
                                'Bash Shell',
                                'Cloud computing',
                                'Networking',
                                'OpenStack',
                                'AWS',
                                'Amazon S3',
                                'Continuous integration/continuous deployment (CI/CD)',
                                'Grafana',
                                'TCP/IP',
                                'Fedora',
                                'Containerization technologies',
                                'Zabbix',
                                'Load Balancing',
                                'Perl',
                                'ELB',
                                'Firewalls',
                                'Google Cloud Platform',
                                'EFS',
                                'Ruby',
                                'Route 53',
                                'Vulnerability Scanning',
                                'Terraform',
                                'CentOS',
                                'Security and compliance',
                                'ELK Stack',
                                'Auto Scaling',
                                'Jenkins',
                                'DNS',
                                'Java',
                                'Scripting languages',
                                'Penetration Testing',
                                'Python'],
            'Systems Analyst': ['Requirement gathering',
                                'Waterfall',
                                'Systems analysis',
                                'Software development life cycle (SDLC)',
                                'Agile',
                                'Process improvement'],
            'Game Developer': ['Gameplay mechanics',
                               'UI/UX design',
                               'Game engines and frameworks',
                               '3D modeling and animation',
                               'Project management',
                               'Programming languages',
                               'Game design principles',
                               'Game physics'],
            'UI/UX Designer': ['User interface design',
                               'Color theory',
                               'JavaScript',
                               'Usability testing',
                               'Prototyping',
                               'Typography',
                               'Information architecture',
                               'HTML/CSS',
                               'Visual design',
                               'Graphic design tools',
                               'Wireframing',
                               'Interaction design',
                               'Wireframing and prototyping tools',
                               'User experience design'],
            'IT Manager': ['Project management','IT governance and compliance','Risk management',
                           'Budgeting and financial management',
                           'IT strategy development',
                           'Vendor management']}

def load_pickle(filename):
    data_file = open(filename, 'rb')
    data = pickle.load(data_file)
    data_file.close()
    return data

tfidf_data_filepath = ('C:/Users/DELL/Desktop/Course_Recommendation/BEProject/SystemCode/Recommendation/FeatureMap/tfidf_data.pickle')
categorical_data_filepath = 'C:/Users/DELL/Desktop/Course_Recommendation/BEProject/SystemCode/Recommendation/FeatureMap/categorical_data.pickle'
tfidf_vectorizer_filepath = 'C:/Users/DELL/Desktop/Course_Recommendation/BEProject/SystemCode/Recommendation/FeatureMap/tfidf_vectorizer.pickle'
# TEXT BASED RECOMMENDATION THRESHOLD
text_thres = 0.2
# MINIMUM FREE COURSE COUNT THRESHOLD
free_show_thres = 20
# RECOMMENDATION RESULTS SIZE
recommend_topn = 50
# DEFAULT POPULAR RESULTS SIZE
recommend_default_topn = 50
# multiplier=5
# what to learn, difficulty,duration.free

stopwordsdic = stopwords.words('english')
lemmatizer = WordNetLemmatizer()
stop_words = stopwords.words('english')

def text_preprocess_jcr(rawtext):
    text = ', '.join(rawtext)  # Join list elements with a comma and space
    # Remove all non ASCII characters
    text = re.sub('([^\x00-\x7F])+', '', text)
    text = text.lower()  # lower casing all words
    text = text.strip()  # Remove White Spaces
    # remove stop words
    text = ' '.join([word for word in text.split() if word not in stop_words])
    text = ' '.join([lemmatizer.lemmatize(word)
                    for word in text.split()])  # lemmatization
    return text

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



def recommend_job_role_based(user_input, rating_data, tfidf_vectorizer, tfidf_data, categorical_data):
    # 1. Feature Extraction - Text Based (TfIdf)
    # Load Tfidf Data Sparse Matrix
    # tfidf_data_file = open(config.tfidf_data_filepath, 'rb')
    # tfidf_data = pickle.load(tfidf_data_file)
    # tfidf_data_file.close()
    # Text Input and Similarity Score
    # get skill set for job role
    skill_set = job_role[user_input[0]]

    # print(skill_set)
    # create TF-IDF vector for skill set
    skill_set_tfidf = tfidf_vectorizer.transform([" ".join(skill_set)])

    text_input = skill_set
    #print('text input:  ',text_input)
    text_processed = text_preprocess_jcr(text_input)
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

    categorical_vect = categorical_encode(categorical_input)

    categorical_sim = cond_sim(
        categorical_vect, categorical_data[:, :-1]).ravel()

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
    rec_sim, rec_idx = ranking(
        free_mask, tfidf_sim, categorical_sim, rating_data)

    # 5. Append paid courses if number of free courses below a threshold
    if (free_mask.sum() < free_show_thres) and (paid_mask.sum() > 0):
        paid_sim, paid_idx = ranking(
            paid_mask, tfidf_sim, categorical_sim, rating_data)
        rec_sim = np.append(rec_sim, paid_sim)
        rec_idx = np.append(rec_idx, paid_idx)

    # 6. Convert Index to courseID
    rec_idx = rec_idx + 1
    course_sim = rec_sim[:recommend_topn].tolist()
    course_idx = rec_idx[:recommend_topn].tolist()
    if len(course_idx)<recommend_topn:
        for s in skill_set:
            inp=[s,user_input[1],user_input[2],user_input[3]]
            c_idx = recommend(inp,rating_data, tfidf_vectorizer, tfidf_data, categorical_data)
            for ijj in c_idx[:5]:

                course_idx.append(ijj)
    return course_idx
#testing
'''ainput = ['DevOps Engineer', 0, 0, 0]
rawdata_rating = rawdata['popularity_index']
a=load_pickle(tfidf_data_filepath)
b=load_pickle(categorical_data_filepath)
c=load_pickle(tfidf_vectorizer_filepath)
idx=recommend_job_role_based(ainput,rawdata_rating,c,a,b)
print(len(idx))
skill=job_role[ainput[0]]
print(skill)
for s in skill:
    inp=[s,ainput[1],ainput[2],ainput[3]]
    c_idx = recommend(inp,rawdata_rating,c,a,b)
    idx.append(c_idx[:5])
for ink in idx:
    print(rawdata['title'][ink])'''

