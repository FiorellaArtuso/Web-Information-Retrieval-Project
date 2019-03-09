from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import unquote
from treetagger import TreeTagger
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from string import punctuation
from random import randint
from utils import *
import os
import requests
import json
import re

chosen_articles = set()

choose_category = 0
wikipedia_categories = [
   'Academic_disciplines‎', 'Arts‎', 'Business‎', 'Concepts‎', 'Culture‎', 'Education‎', 'Entertainment', 'Events‎', 'Geography‎', 'Health‎',
   'History', 'Humanities‎', 'Language‎', 'Law', 'Life‎', 'Mathematics‎', 'Nature', 'People‎', 'Philosophy‎', 'Politics', 'Reference‎',
   'Religion‎', 'Science‎', 'Society‎', 'Sports‎', 'Technology‎', 'World‎'
   ]

def normalize(sentence_to_normalize):
    print_coloured_bold('Sentence to stem:',"green")
    print(sentence_to_normalize + '\n')

    #removing m-dash
    sentence_to_normalize = sentence_to_normalize.replace("–"," ").lower()
    sentence_to_normalize = re.sub("-{2,}","",sentence_to_normalize)

    #removing contract forms
    if("'t" in sentence_to_normalize):
        sentence_to_normalize = sentence_to_normalize.replace("'t","")

    #removing specifications inside parenthesis
    start = sentence_to_normalize.find( '(' )
    end = sentence_to_normalize.find( ')' )
    if start != -1 and end != -1:
      sentence_to_normalize = sentence_to_normalize.replace(sentence_to_normalize[start:end+1],"")

    #tokenization
    word_tokens = word_tokenize(sentence_to_normalize)

    #punctuation removal
    word_tokens_filtered = [w for w in word_tokens if not w in punctuation and not w=="'s"]

    #skip if punctuation within words (except -./) or split if / within word
    word_tokens_noslash = list()
    for w in word_tokens_filtered:
        if any(char in punctuation.replace("-","").replace(".","").replace("/","") for char in w):
            return False
        if "/" in w:
            words = w.split("/")
            for split in words:
                if not split == "":
                    word_tokens_noslash.append(split)
        else:
            word_tokens_noslash.append(w)

    #leave acronyms and split others in case of .
    word_tokens_dot = list()
    regex = re.compile('(?:[a-z]\.){2,}')
    for w in word_tokens_noslash:
        if(w+"." in sentence_to_normalize and regex.match(w+".")):
            word_tokens_dot.append(w)
        elif("." in w):
            words = w.split(".")
            for split in words:
                if not split == "":
                    word_tokens_dot.append(split)
        else:
            word_tokens_dot.append(w)

    #stopwords removal (done before stemming, less words to stem)
    stop_words = set(stopwords.words('english'))
    no_stopwords_sentence = [w for w in word_tokens_dot if not w in stop_words]

    #digits removal
    sentence_words_nodigits = [w for w in no_stopwords_sentence if not w.isdigit()]

    #roman numerals removal
    regex = re.compile('^(?=[MDCLXVI])M*D?C{0,4}L?X{0,4}V?I{0,4}$')
    no_roman_numerals_sentence = [w for w in sentence_words_nodigits if not regex.match(w)]

    #one letter words removal
    sentence_words_nosingleletters = [w for w in no_roman_numerals_sentence if not len(w)<2]
    #print('No one letter words:')

    #stemming
    stemmed_sentence = ""
    stemmer = TreeTagger(path_to_treetagger='/home/biar/Desktop/ProgettoWIR/treetagger')
    for word in sentence_words_nosingleletters:
        stem = stemmer.tag(word)
        if not(stem[0][1] == "CRD"):
            if not stem[0][2] == '<unknown>':
                if '|' in stem[0][2]:
                    first_word = ((stem[0][2]).split('|'))[0]
                    stem[0][2] = first_word
                    if(len(first_word)>1):
                        stemmed_sentence += (correct_stemming(stem).lower() + " ")
                else:
                    if(len((stem[0][2]).lower())>1):
                        stemmed_sentence += (correct_stemming(stem).lower() + " ")
            else:
                stemmed_sentence += ((stem[0][0]).lower() + " ")

    print_coloured_bold('Stemmed sentence:',"yellow")
    print(stemmed_sentence.strip())
    print('\n')
    return stemmed_sentence.strip()

def add_article_to_corpus(filename):
    global choose_category
    depth = randint(0,3)
    print_coloured_bold("main category","cyan")
    print(wikipedia_categories[choose_category % 27])
    current_category = wikipedia_categories[choose_category % 27]
    if (depth > 0):
        skos = ""
        for i in range(depth-1):
            skos += '?/skos:broader'
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""SELECT distinct ?subcategoryLabel WHERE
          {{
          ?subcategory skos:broader{} <http://dbpedia.org/resource/Category:{}>.
          ?subcategory rdfs:label ?subcategoryLabel
          }}
          """.format(skos, wikipedia_categories[choose_category % 27].replace(u'\u200e', '')))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        subcategories = list()
        for result in results["results"]["bindings"]:
            subcategories.append(result["subcategoryLabel"]["value"])
        if len(subcategories) == 0:
            return False
        current_category = subcategories[randint(0,len(subcategories)-1)]

    print_coloured_bold("current category","cyan")
    print(current_category)

    req = requests.post("https://en.wikipedia.org/wiki/Special:RandomInCategory", data={'wpcategory': current_category })
    name = req.url.split("/")[-1]
    article_name = unquote(req.url.split("/")[-1]).replace("_", " ")
    if "Category:" in article_name or "Special:RandomInCategory" in article_name:
        return False
    if not article_name in chosen_articles:
        print_coloured_bold('\nTITLE: ' + article_name + '\n', "blue")

        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""
            SELECT ?categoryLabel, ?redirectionsLabels
            WHERE {
            {
            <http://dbpedia.org/resource/articleName> dct:subject ?category.
            ?category rdfs:label ?categoryLabel
            }
            UNION
            {
            ?redirections  dbo:wikiPageRedirects <http://dbpedia.org/resource/articleName>.
            ?redirections  rdfs:label ?redirectionsLabels
            }
            }
            """.replace("articleName", name))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        categories_list = {wikipedia_categories[choose_category % 27].replace(u'\u200e', '').replace("_"," ")}
        redirections_list = set()

        if results["results"]["bindings"]:
            for result in results["results"]["bindings"]:
                keys = result.keys()
                #remove administrative categories
                if ("categoryLabel" in keys and result["categoryLabel"]["value"] not in administrative_categories_set):
                    #merge stub categories with the actual ones
                    if ("stubs" in result["categoryLabel"]["value"]):
                        categories_list.add((result["categoryLabel"]["value"]).replace("stubs",""))
                    elif ("stub" in result["categoryLabel"]["value"]):
                        categories_list.add((result["categoryLabel"]["value"]).replace("stub",""))
                    else:
                        categories_list.add(result["categoryLabel"]["value"])
                elif ("redirectionsLabels" in keys):
                    redirections_list.add(result["redirectionsLabels"]["value"])

        #skip if article is not present on dbpedia
        if( len(categories_list) == 0 and len(redirections_list) == 0):
            return False

        print_coloured_bold('Categories:',"cyan")
        print(categories_list)
        print('\n')
        print_coloured_bold('Redirections:',"cyan")
        print(redirections_list)
        print('\n')

        print_coloured_bold('# NORMALIZING TITLE #\n', "darkcyan")
        normalized_article = normalize(article_name)
        if(normalized_article == False):
            return False
        print_coloured_bold("normalized article:","red")
        print(normalized_article)


        print_coloured_bold('\n# NORMALIZING REDIRECTIONS #\n',"darkcyan")
        normalized_redirections = list()
        normalized_redirections.append(normalized_article)
        for redirection in redirections_list:
            normalized_redirection = normalize(redirection)
            if(normalized_redirection == False):
                return False
            if not normalized_redirection in normalized_redirections:
                normalized_redirections.append(normalized_redirection)
        print_coloured_bold("normalized redirecitons:","red")
        print(normalized_redirections)

        write_article_to_file(filename, article_name, normalized_redirections, categories_list)
        choose_category += 1
        chosen_articles.add(article_name)
        return True
    else:
        return False

def create_intermediate_dataset(numberOfArticles):
    filename = str(time.time()).replace(".","")+".txt"
    path = os.path.join('./ArticlesToMerge', filename )
    with open(path, "w") as f:
        f.write(str(numberOfArticles) +"\n")
    count=0
    while(count < numberOfArticles):
        print_coloured_bold("\n################################ ARTICLE N° "+ str(count) +" ################################", "purple")
        if (add_article_to_corpus(filename)):
            count+=1

administrative_categories_set = administrative_categories_set()
create_intermediate_dataset(1000)


