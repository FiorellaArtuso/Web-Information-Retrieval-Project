from SPARQLWrapper import SPARQLWrapper, JSON
from nltk.corpus import stopwords
import os
import json
import time

purple = '\033[95m'
cyan = '\033[96m'
darkcyan = '\033[36m'
blue = '\033[94m'
green = '\033[92m'
yellow = '\033[93m'
red = '\033[91m'
bold = '\033[1m'
end = '\033[0m'

def print_dictionary(dictionary):
    for k,v in dictionary.items():
        print(red+bold+"{}".format(k)+end+":{}".format(v))

def print_categories(dictionary):
  for k,v in dictionary.items():
      print(red+bold+"{}".format(k)+end+":{}".format(v['num_articles']))

def print_coloured_bold(sentence,colour):
    if(colour == "purple"):
        print(purple+bold+sentence+end)
    elif(colour == "cyan"):
        print(cyan+bold+sentence+end)
    elif(colour == "darkcyan"):
        print(darkcyan+bold+sentence+end)
    elif(colour == "blue"):
        print(blue+bold+sentence+end)
    elif(colour == "green"):
        print(green+bold+sentence+end)
    elif(colour == "yellow"):
        print(yellow+bold+sentence+end)
    elif(colour == "red"):
        print(red+bold+sentence+end)
    else:
        print(bold+sentence+end)

def correct_stemming(stem):
    stop_words = set(stopwords.words("english"))
    if(not stem[0][2] in stop_words):
        return stem[0][2]
    return stem[0][0]

def write_dictionary_to_JSONfile(dictionary,filename):
    for key, value in dictionary.items():
        dictionary[key] = repr(value)
    path = os.path.join('./Dataset', filename + '.json')
    with open(path, 'w') as fp:
        json.dump(dictionary, fp)

def write_JSONfile_to_dictionary(filename):
    path = os.path.join('./Dataset', filename + '.json')
    with open(path, 'r') as fp:
        data = json.load(fp)
        for key, value in data.items():
            data[key] = eval(value)
        return data

def write_article_to_file(filename, article, redirections, categories):
    path = os.path.join('./ArticlesToMerge', filename )
    with open(path, "a") as f:
        f.write(article +"\n")
        f.write(str(redirections)+"\n")
        f.write(str(categories)+"\n")


def retrieve_article_from_file(filename):
    with open("test.txt", "r") as f:
        print (eval(f.readline()))
        print (eval(f.readline()))

def administrative_categories_set():
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery("""
        SELECT distinct ?subcategoryLabel WHERE
        {
        ?subcategory skos:broader?/skos:broader?/skos:broader <http://dbpedia.org/resource/Category:Wikipedia_administration>.
        ?subcategory rdfs:label ?subcategoryLabel
        }
        """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    administrative_categories_set = set()
    for result in results["results"]["bindings"]:
        administrative_categories_set.add(result["subcategoryLabel"]["value"])
    return administrative_categories_set


