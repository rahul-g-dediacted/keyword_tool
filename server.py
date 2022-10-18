import os
import json
import re
import sys
import requests

from bs4 import BeautifulSoup

from nltk.corpus import stopwords
from nltk import ngrams

from random import shuffle

from collections import Counter

from flask import Flask, jsonify, render_template
from flask_cors import CORS, cross_origin

import operator

from selenium import webdriver
from selenium.webdriver.common.by import By

from tqdm import tqdm

from datetime import datetime
from multiprocessing import Process
from threading import Thread

import traceback

import pymongo

app = Flask(__name__,static_folder='build/static', template_folder='build')
cors = CORS(app,resource={
    r"/*":{
        "origins":"*"
    }
})

@app.route('/')
@cross_origin()
def index():
    return render_template('index.html')

@app.route('/words/<params>')
@cross_origin()
def words(params):    

    print(datetime.now())
    
    split = params.split('_')
    query = split[0]
    host = split[1]

    gl = host[-2:]
    lr = f'lang_{gl}'    

    urls = []
    remove_url = []
    
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options,executable_path='/home/ubuntu/sw/chromedriver')

    driver.get(f'https://www.{host}/search?q={query}&num=50&gl={gl}&lr={lr}')

    search = driver.find_elements_by_class_name("yuRUbf")
    
    for s in search:
        link = s.find_element_by_tag_name("a")
        li = link.get_attribute('href')
        if li != None:
            if(not re.search('(.youtube.)|(.google.)|(.pdf)',li)):
                urls.append(li)    

    monos_related = []
    bis_related = []    
    tris_related = []    
    
    request = os.popen(f"python3 /home/ubuntu/sw/google-ads-python/examples/planning/generate_keyword_ideas.py -c 7080644452 -k {query}").read()

    # request = open('keywords.txt','r').read()

    split = request.split('\n')    

    for s in split:
        if s != '':
            s = s.split('"')[1]
            if len(s.split(' ')) == 1:
                monos_related.append({
                    'Keyword':s,
                    'TF':[],
                    'Occur':0,
                    'WC':[],
                    'DF':0,
                })
            elif len(s.split(' ')) == 2:
                bis_related.append({
                    'Keyword':s,
                    'TF':[],
                    'Occur':0,
                    'WC':[],
                    'DF':0,
                })
            else:
                tris_related.append({
                    'Keyword':s,
                    'TF':[],
                    'Occur':0,
                    'WC':[],
                    'DF':0,
                })    

    monos = []
    bis = []
    tris = []

    bis_preps = []
    bis_conjs = []    

    exact = {
        'Keyword':query,
        'TF':0,
        'Occur':0,
        'WC':0,
        'DF':0,
    }
    exact_tf = []
    exact_wc = []

    for u in tqdm(urls):
        try:
            raw = []
            request = requests.get(u,timeout=10)
            string_content = request.text
            html = request.content
            dom = BeautifulSoup(html,'html.parser')
            dom = list(dom.stripped_strings)            

            for do in dom:
                do = do.split(' ')
                for d in do:
                    raw.append(d)

            raw = [word.lower() for word in raw]

            text = []        
            remove = '"!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~"'
            for r in raw:
                for rem in remove:
                    r = r.replace(rem,'')
                text.append(r)
            
            text = [word for word in text if word != '']
            text = [word for word in text if len(word)>2]
            text = [word for word in text if not word.isnumeric()]        

            wc = len(text)                

            tri = list(ngrams(text,3))
            tri = [' '.join(t) for t in tri]
            tri_count = dict(Counter(tri))

            tri_list = []
            for t in tri_count:
                tri_list.append({
                    'keyword':t,
                    'count':tri_count[t]
                })  
            
            if(re.search(query,string_content)):
                all_occcur = re.findall(query,string_content)                            
                exact['Occur'] +=1                
                exact_tf.append(len(all_occcur))
                exact_wc.append(wc)                

            bi = list(ngrams(text,2))
            bi = [' '.join(b) for b in bi]

            bi_count = dict(Counter(bi))

            bi_list = []
            for b in bi_count:
                bi_list.append({
                    'keyword':b,
                    'count':bi_count[b]
                })            

            prepositions = ['di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra']            
            for p in prepositions:
                for b in bi_list:                    
                    word = b['keyword'].split(' ')                
                    word.insert(1,p)
                    word = ' '.join(word)
                    bis_preps.append({
                        'Keyword':word,
                        'TF':[],
                        'Occur':0,
                        'WC':[],
                        'DF':0,
                    })            

            for b in bis_preps:
                for bi in tri_list:
                    if b['Keyword'] == bi['keyword']:                        
                        b['Occur'] +=1
                        b['TF'].append(bi['count'])
                        b['WC'].append(len(tri_list))                
                        tri_list.remove(bi)                    
            
            conjunctions = ['e','é','o']       
            for c in conjunctions:
                for b in bi_list:
                    word = b['keyword'].split(' ')
                    word.insert(1,c)
                    word = ' '.join(word)
                    bis_conjs.append({
                        'Keyword':word,
                        'TF':[],
                        'Occur':0,
                        'WC':[],
                        'DF':0,
                    })

            for b in bis_conjs:
                for bi in tri_list:
                    if b['Keyword'] == bi['keyword']:                        
                        b['Occur'] +=1
                        b['TF'].append(bi['count'])
                        b['WC'].append(len(tri_list))
                        tri_list.remove(bi)
            
            
            for b in bis_related:
                for bi in bi_list:
                    if b['Keyword'] == bi['keyword']:
                        b['TF'].append(bi['count'])                        
                        b['Occur'] +=1
                        b['WC'].append(len(bi_list))
                        bi_list.remove(bi)        

            for b in bi_list:
                bis.append({
                    'keyword':b['keyword'],
                    'tf':b['count'],
                    'df':0,
                    'wc':wc
                })            


            for t in tris_related:
                for tri in tri_list:
                    if t['Keyword'] == tri['keyword']:
                        t['TF'].append(tri['count'])                        
                        t['Occur'] +=1
                        t['WC'].append(len(tri_list))                        
                        tri_list.remove(tri)            

            for t in tri_list:
                obj = {
                    'keyword':t['keyword'],
                    'tf':t['count'],
                    'df':0,
                    'wc':wc
                }
                tris.append(obj)
            
            mono_list = []

            text = [word for word in text if word not in stopwords.words('english')]
            text = [word for word in text if word not in stopwords.words('italian')]
            text = [word for word in text if word not in stopwords.words('french')]
            text = [word for word in text if word != '']

            mono_count = dict(Counter(text))
            
            for m in mono_count:
                mono_list.append({
                    'keyword':m,
                    'count':mono_count[m]
                })            
                    
            for m in monos_related:
                for mo in mono_list:
                    if m['Keyword'] == mo['keyword']:
                        m['TF'].append(mo['count'])
                        m['WC'].append(len(mono_list))                        
                        m['Occur'] +=1                     
                        mono_list.remove(mo)        

            for m in mono_list:
                monos.append({
                    'keyword':m['keyword'],
                    'tf':m['count'],
                    'df':0,
                    'wc':wc
                })            

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            remove_url.append(u)

    length = len(urls)-len(remove_url)

    exact['TF'] = sum(exact_tf)/len(exact_tf)
    exact['WC'] = int(sum(exact_wc)/len(exact_wc))    
    exact['TF'] = round((exact['TF']/exact['WC'])*100,2)

    for b in tqdm(bis_preps):
        if len(b['TF']) == 0:
            b['TF'] = 0
        else:
            b['TF'] = sum(b['TF'])/len(b['TF'])
            b['WC'] = int(sum(b['WC'])/len(b['WC']))    
            b['TF'] = round((b['TF']/b['WC'])*100,2)

    for b in tqdm(bis_conjs):
        if len(b['TF']) == 0:
            b['TF'] = 0
        else:
            b['TF'] = sum(b['TF'])/len(b['TF'])
            b['WC'] = int(sum(b['WC'])/len(b['WC']))    
            b['TF'] = round((b['TF']/b['WC'])*100,2)

    for b in tqdm(monos_related):
        if len(b['TF']) == 0:
            b['TF'] = 0
        else:
            b['TF'] = sum(b['TF'])/len(b['TF'])
            b['WC'] = int(sum(b['WC'])/len(b['WC']))    
            b['TF'] = round((b['TF']/b['WC'])*100,2)

    for b in tqdm(bis_related):
        if len(b['TF']) == 0:
            b['TF'] = 0
        else:
            b['TF'] = sum(b['TF'])/len(b['TF'])
            b['WC'] = int(sum(b['WC'])/len(b['WC']))    
            b['TF'] = round((b['TF']/b['WC'])*100,2)

    for b in tqdm(tris_related):
        if len(b['TF']) == 0:
            b['TF'] = 0
        else:
            b['TF'] = sum(b['TF'])/len(b['TF'])
            b['WC'] = int(sum(b['WC'])/len(b['WC']))    
            b['TF'] = round((b['TF']/b['WC'])*100,2)

    monograms = []

    reject_words = set()
    for m in tqdm(monos):
        word = m['keyword']
        if word not in reject_words:
            tf = []
            wc = []
            df = m['df']
            occur = m['df']
            for mo in monos:
                if word == mo['keyword']:
                    tf.append(mo['tf'])
                    wc.append(mo['wc'])
                    df+=1
                    occur+=1
            reject_words.add(word)
            tf = sum(tf)/len(tf)
            wc = int(sum(wc)/len(wc))
            tf = round((tf/wc)*100,2)
            df = round((df/length)*100,2)
            monograms.append({
                'Keyword':word,
                'TF':tf,
                'Occur':occur,
                'WC':wc,
                'DF':df,
            })

    bigrams = []

    reject_words = set()
    for b in tqdm(bis):
        word = b['keyword']
        if word not in reject_words:
            tf = []
            wc = []
            df = b['df']
            occur = b['df']
            for bi in bis:
                if word == bi['keyword']:
                    tf.append(bi['tf'])
                    wc.append(bi['wc'])
                    df+=1
                    occur+=1
            reject_words.add(word)
            tf = sum(tf)/len(tf)
            wc = int(sum(wc)/len(wc))
            tf = round((tf/wc)*100,2)
            df = round((df/length)*100,2)
            bigrams.append({
                'Keyword':word,
                'TF':tf,
                'Occur':occur,
                'WC':wc,
                'DF':df,
            })

    trigrams = []
    reject_words = set()
    for t in tqdm(tris):
        word = t['keyword']
        if word not in reject_words:
            tf = []
            wc = []
            df = t['df']
            occur = t['df']
            for tri in tris:
                if word == tri['keyword']:
                    tf.append(tri['tf'])
                    wc.append(tri['wc'])
                    df+=1
                    occur+=1
            reject_words.add(word)
            df = round((df/length)*100,2)
            tf = sum(tf)/len(tf)
            wc = int(sum(wc)/len(wc))
            tf = round((tf/wc)*100,2)
            trigrams.append({
                'Keyword':word,
                'TF':tf,
                'Occur':occur,
                'WC':wc,
                'DF':df,
            })

    for m in tqdm(monos_related):        
        m['DF']=round((int(m['Occur'])/length)*100,2)
    for b in tqdm(bis_related):        
        b['DF']=round((int(b['Occur'])/length)*100,2)        
    for t in tqdm(tris_related):        
        t['DF']=round((int(t['Occur'])/length)*100,2)        

    mono_related=[]
    for m in tqdm(monos_related):
        if int(m['DF'])>0:
            mono_related.append(m)

    bi_related=[]
    for m in tqdm(bis_related):
        if int(m['DF'])>0:
            bi_related.append(m)
    
    tri_related=[]
    for m in tqdm(tris_related):
        if int(m['DF'])>0:
            tri_related.append(m)
        
    exact['DF']=round((int(exact['Occur'])/length)*100,2)

    for m in tqdm(bis_conjs):        
        m['DF']=round((int(m['Occur'])/length)*100,2)
    for b in tqdm(bis_preps):        
        b['DF']=round((int(b['Occur'])/length)*100,2)    

    bi_prep=[]
    for b in bis_preps:
        if int(b['DF'])>0:
            bi_prep.append(b)

    bi_conj=[]
    for b in bis_conjs:
        if int(b['DF'])>0:
            bi_conj.append(b)

    prepositions = [' di ', ' a ', ' da ', ' in ', ' con ', ' su ', ' per ', ' tra ', ' fra ']
    conjunctions = [' e ', ' anche ', ' né ',' ma ',' però ',' infatti ',' come ',' dunque ',' perché ',' o ', ' inoltre ', ' oppure ',' nemmeno ',' neanche ',' neppure ',' nemmeno ', ' neanche ',' neppure ',' affinché ',' cosí che ',' mentre ',' quando ',' appena ', ' non appena ',' prima di ',' prima che ',' dopo chi ',' dopo di ',' cioè ',' allora ',' quindi ']

    trigrams_preps = []
    for t in tqdm(trigrams):
        for pc in prepositions:
            if re.search(pc,t['Keyword']):
                trigrams_preps.append(t)    

    trigrams_conj = []
    for t in tqdm(trigrams):
        for pc in conjunctions:
            if re.search(pc,t['Keyword']):
                trigrams_conj.append(t)

    monograms.sort(key=operator.itemgetter('DF'),reverse=True)
    bigrams.sort(key=operator.itemgetter('DF'),reverse=True)
    trigrams.sort(key=operator.itemgetter('DF'),reverse=True)
    mono_related.sort(key=operator.itemgetter('DF'),reverse=True)
    bi_related.sort(key=operator.itemgetter('DF'),reverse=True)
    tri_related.sort(key=operator.itemgetter('DF'),reverse=True)
    bi_prep.sort(key=operator.itemgetter('DF'),reverse=True)
    bi_conj.sort(key=operator.itemgetter('DF'),reverse=True)
    trigrams_preps.sort(key=operator.itemgetter('DF'),reverse=True)
    trigrams_conj.sort(key=operator.itemgetter('DF'),reverse=True)

    monograms_return = monograms[:100]
    bigrams_return = bigrams[:100]
    trigrams_return = trigrams[:100]
    mono_related_return = mono_related[:100]
    bi_related_return = bi_related[:100]
    tri_related_return = tri_related[:100]
    bi_prep_return = bi_prep[:100]
    bi_conj_return = bi_conj[:100]
    trigrams_preps_return = trigrams_preps[:100]
    trigrams_conj_return = trigrams_conj[:100]

    mongo = pymongo.MongoClient("mongodb+srv://wosnic:Lorenapasqualato@cluster0.58w91.mongodb.net/seodb?authSource=admin&replicaSet=Cluster0-shard-0&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&ssl=true")
    sw = mongo["sw"]

    monograms_col = sw["monograms"]    
    monograms_insert = {
        'keyword':query,
        'monograms':monograms[:100]
    }
    insert = monograms_col.insert_one(monograms_insert)
    print(insert.inserted_id)

    bigrams_col = sw['bigrams']
    bigrams_insert = {
        'keyword':query,
        'bigrams':bigrams[:100]
    }
    insert = bigrams_col.insert_one(bigrams_insert)
    print(insert.inserted_id)

    trigrams_col = sw['trigrams']
    trigrams_insert = {
        'keyword':query,
        'trigrams':trigrams[:100]
    }
    insert = trigrams_col.insert_one(trigrams_insert)
    print(insert.inserted_id)

    monograms_related_col = sw['monograms_related']
    monos_related_insert = {
        'keyword':query,
        'monograms_related':mono_related[:100]
    }
    insert = monograms_related_col.insert_one(monos_related_insert)
    print(insert.inserted_id)

    bigrams_related_col = sw['bigrams_related']
    bis_related_insert = {
        'keyword':query,
        'bigrams_related':bi_related[:100]
    }
    insert = bigrams_related_col.insert_one(bis_related_insert)
    print(insert.inserted_id)

    trigrams_related_col = sw['trigrams_related']
    tris_related_insert = {
        'keyword':query,
        'trigrams_related':tri_related[:100]
    }
    insert = trigrams_related_col.insert_one(tris_related_insert)
    print(insert.inserted_id)

    trigrams_preps_col = sw['trigrams_prepositions']
    trigrams_preps_insert = {
        'keyword':query,
        'trigrams_prepositions':trigrams_preps[:100]
    }
    insert = trigrams_preps_col.insert_one(trigrams_preps_insert)
    print(insert.inserted_id)

    trigrams_conj_col = sw['trigrams_conjunctions']
    trigrams_conj_insert = {
        'keyword':query,
        'trigrams_conjunctions':trigrams_conj[:100]
    }
    insert = trigrams_conj_col.insert_one(trigrams_conj_insert)
    print(insert.inserted_id)

    bi_prep_col = sw['bigrams_prepositions']
    bi_prep_insert = {
        'keyword':query,
        'bigrams_prepositions':bi_prep[:100]
    }
    insert = bi_prep_col.insert_one(bi_prep_insert)
    print(insert.inserted_id)

    bi_conj_col = sw['bigrams_conjunctions']
    bi_conj_insert = {
        'keyword':query,
        'bigrams_conjunctions':bi_conj[:100]
    }
    insert = bi_conj_col.insert_one(bi_conj_insert)
    print(insert.inserted_id)

    exact_col = sw['exact']    
    exact_insert = {
        'keyword':query,
        'exact':[exact]
    }
    insert = exact_col.insert_one(exact_insert)
    print(insert.inserted_id)

    allgrams = monograms_return + bigrams_return + trigrams_return
    allgrams += mono_related_return + bi_related_return + tri_related_return
    allgrams += bi_prep_return + bi_conj_return
    allgrams += trigrams_preps_return + trigrams_conj_return    

    allgrams.sort(key=operator.itemgetter('DF'),reverse=True)            

    allgrams.insert(0,exact)

    final = []
    for a in allgrams:
        if int(a['DF']) != 0:
            final.append(a)            

    print(len(final))

    return jsonify({
        'allgrams':final
    })

if __name__ == '__main__':    
    app.run(debug=True)
