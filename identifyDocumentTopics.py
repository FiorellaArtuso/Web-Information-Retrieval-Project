from treetagger import TreeTagger
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from string import punctuation
from math import log10
from prettytable import PrettyTable
from utils import *
import os
import requests
import json
import re


def normalize_document(pathname, filename):
    document_words = dict()
    path = os.path.join(pathname, filename)
    with open(path, 'r') as document:
        for line in document:
            sentence_to_normalize = line.strip()
            if len(sentence_to_normalize) == 0:
                continue
            print_coloured_bold('\nSentence to stem: ' + sentence_to_normalize + '\n',"red")

            #removing m-dash
            sentence_to_normalize = sentence_to_normalize.replace("–"," ").lower()
            sentence_to_normalize = re.sub("-{2,}","",sentence_to_normalize)

            #removing contract forms
            if("'t" in sentence_to_normalize):
                sentence_to_normalize = sentence_to_normalize.replace("'t","")

            #tokenization
            word_tokens = word_tokenize(sentence_to_normalize)

            #punctuation removal
            word_tokens_filtered = [w for w in word_tokens if not w in punctuation and not w=="'s"]

            #skip if punctuation within words (except -./) or split if / within word
            word_tokens_noslash = list()
            for w in word_tokens_filtered:
                if not any(char in punctuation.replace("-","").replace(".","").replace("/","") for char in w):
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
            print_coloured_bold("Stop words result","cyan")
            print(sentence_words_nosingleletters)
            print('\n')

            #stemming
            stemmer = TreeTagger(path_to_treetagger='/home/biar/Desktop/ProgettoWIR/treetagger')
            for word in sentence_words_nosingleletters:
                stem = stemmer.tag(word)
                if not(stem[0][1] == "CRD"):
                    if not stem[0][2] == '<unknown>':
                        if '|' in stem[0][2]:
                            first_word = ((stem[0][2]).split('|'))[0]
                            stem[0][2] = first_word
                            if(len(first_word)>1):
                                w = correct_stemming(stem).lower()
                                if not w in document_words:
                                    document_words[w] = 1
                                else:
                                    document_words[w]+=1
                        else:
                            if(len((stem[0][2]).lower())>1):
                                w = correct_stemming(stem).lower()
                                if not w in document_words:
                                    document_words[w] = 1
                                else:
                                    document_words[w]+=1
                    else:
                        w = (stem[0][0]).lower()
                        if not w in document_words:
                            document_words[w] = 1
                        else:
                            document_words[w]+=1
    return document_words

def identify_topics(pathname, filename):
    document_words = normalize_document(pathname,filename)
    stems = write_JSONfile_to_dictionary('stems')
    stemmed_titles = write_JSONfile_to_dictionary('stemmed_titles')
    articles = write_JSONfile_to_dictionary('articles')
    categories = write_JSONfile_to_dictionary('categories')

    #words in common between document and dataset
    common_words = set(stems.keys()).intersection(set(document_words.keys()))

    #computing words weights
    words_weights = dict()
    number_wikipedia_categories = len(categories.keys())
    for word in common_words:
        term_frequency = document_words[word]
        category_frequency = 0
        for key,value in categories.items():
            if word in value['vocabulary']:
                category_frequency+=1
        words_weights[word] = term_frequency * log10(number_wikipedia_categories/category_frequency)

    #computing supporting words for each title
    titles_supporting_words = dict()
    for word in common_words:
        titles_word = stems[word]
        for t in titles_word:
            title_tokens = t.split(" ")
            title_tokens.remove(word)
            tokens_present_in_doc = [token for token in title_tokens if token in document_words]
            if (len(tokens_present_in_doc) >= len(title_tokens)-1):
                if t not in titles_supporting_words:
                    titles_supporting_words[t] = set()
                titles_supporting_words[t].add(word)

    #computing titles weights
    titles_weights = dict()
    for key,value in titles_supporting_words.items():
        title_weight = 0
        at = len(stemmed_titles[key])
        lt = len(key.split(" "))
        st = len([token for token in key.split(" ") if token in document_words])
        for supporting_word in value:
            rw = words_weights[supporting_word]
            tw = len(stems[supporting_word])
            title_weight += rw * (1/tw)
        titles_weights[key] = title_weight * (1/at) * (st/lt)

    #computing articles weights
    articles_weights = dict()
    for key,value in titles_weights.items():
        title_articles = stemmed_titles[key]
        for article in title_articles:
            if article not in articles_weights:
                articles_weights[article] = value
            else:
                articles_weights[article]= max(value, articles_weights[article])

    #computing categories weights
    categories_weights = dict()
    for key,value in articles_weights.items():
        categories_list = articles[key]
        for category in categories_list:
            if (category not in categories_weights):
                categories_weights[category] = value
            else:
                categories_weights[category] += value

    categories_weights_sorted = sorted(categories_weights.items(), key=lambda kv: kv[1])
    categories_weights_sorted.reverse()

    #computing  supporting words of category
    supporting_words_categories = dict()
    for key,value in titles_supporting_words.items():
        pointed_articles = stemmed_titles[key]
        for a in pointed_articles:
            article_categories = articles[a]
            for c in article_categories:
                if c not in supporting_words_categories:
                    supporting_words_categories[c] = set()
                supporting_words_categories[c].update(value)

    #computing categories weights opt1
    for key,value in categories_weights.items():
        vc = len(supporting_words_categories[key])
        dc = len(categories[key]["vocabulary"])
        categories_weights[key] *= vc/dc

    categories_weights_sorted_opt1 = sorted(categories_weights.items(), key=lambda kv: kv[1])
    categories_weights_sorted_opt1.reverse()

    #computing categories weights opt2
    words_decay_values = dict()
    for word in common_words:
        words_decay_values[word] = 1

    for c in categories_weights_sorted_opt1:
        supporting_words_c = supporting_words_categories[c[0]]
        total_dw = 0
        for w in supporting_words_c:
            total_dw += words_decay_values[w]
            words_decay_values[w]/=2
        categories_weights[c[0]] *= total_dw/ len(supporting_words_c)

    print_coloured_bold("\n###########CATEGORIES WEIGHTS OPT###########", "cyan")
    categories_weights_sorted_opt2 = sorted(categories_weights.items(), key=lambda kv: kv[1])
    categories_weights_sorted_opt2.reverse()
    t = PrettyTable(['PRE-OPT', 'OPT1','OPT2'])
    result = list()
    for i in range(0,20):
        result.append(categories_weights_sorted_opt2[i][0])
        t.add_row(
            [categories_weights_sorted[i][0]+": "+str(categories_weights_sorted[i][1]),
            categories_weights_sorted_opt1[i][0]+": "+str(categories_weights_sorted_opt1[i][1]),
            categories_weights_sorted_opt2[i][0]+": "+str(categories_weights_sorted_opt2[i][1])])
    print(t)
    return result

#identify_topics('./Documents','49960')

