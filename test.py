from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import unquote
from identifyDocumentTopics import *
from random import randint
from utils import *
import matplotlib.pyplot as plt
import collections
import wikipedia
import requests
import os

wikipedia_categories = [
   'Academic_disciplines‎', 'Arts‎', 'Business‎', 'Concepts‎', 'Culture‎', 'Education‎', 'Entertainment', 'Events‎', 'Geography‎', 'Health‎',
   'History', 'Humanities‎', 'Language‎', 'Law', 'Life‎', 'Mathematics‎', 'Nature', 'People‎', 'Philosophy‎', 'Politics', 'Reference‎',
   'Religion‎', 'Science‎', 'Society‎', 'Sports‎', 'Technology‎', 'World‎'
   ]

def correct_categories_percentage(pathname, filename, article_name, file_result):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery("""
            SELECT ?categoryLabel
            WHERE {
            <http://dbpedia.org/resource/articleName> dct:subject ?category.
            ?category rdfs:label ?categoryLabel
            }
            """.replace("articleName", article_name))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    official_categories = set()

    if results["results"]["bindings"]:
        for result in results["results"]["bindings"]:
            #merge stub categories with the actual ones
            if ("stubs" in result["categoryLabel"]["value"]):
                official_categories.add((result["categoryLabel"]["value"]).replace("stubs",""))
            elif ("stub" in result["categoryLabel"]["value"]):
                official_categories.add((result["categoryLabel"]["value"]).replace("stub",""))
            else:
                official_categories.add(result["categoryLabel"]["value"])

    if(len(official_categories) == 0):
        return False

    #removing official categories not present in our category dictionary
    categories = write_JSONfile_to_dictionary('categories')
    official_categories = official_categories.intersection(set(categories.keys()))

    if(len(official_categories) == 0):
        return False


    top20_categories = identify_topics(pathname, filename)


    exact_match_categories_top20 = official_categories.intersection(top20_categories)

    print_coloured_bold("official categories exact match: ", "cyan")
    print(official_categories)

    print_coloured_bold("selected categories exact match: ", "cyan")
    print(exact_match_categories_top20)

    percentage_exact_match = len(exact_match_categories_top20)/len(official_categories)
    print_coloured_bold("percentage exact-match: ", "cyan")
    print(percentage_exact_match)

    #first relaxation of requirements
    categories_dist1 = set()
    categories_dist1.update(exact_match_categories_top20)
    for category in official_categories.difference(exact_match_categories_top20):
        #taking sub-categories dist-max = 1
        subcategories = set()
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""SELECT distinct ?subcategoryLabel WHERE
              {{
              ?subcategory skos:broader <http://dbpedia.org/resource/Category:{}>.
              ?subcategory rdfs:label ?subcategoryLabel
              }}
              """.format(category.replace(u'\u200e', '').replace(" ","_")))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            for result in results["results"]["bindings"]:
                if ("stubs" in result["subcategoryLabel"]["value"]):
                    subcategories.add((result["subcategoryLabel"]["value"]).replace("stubs",""))
                elif ("stub" in result["subcategoryLabel"]["value"]):
                    subcategories.add((result["subcategoryLabel"]["value"]).replace("stub",""))
                else:
                    subcategories.add(result["subcategoryLabel"]["value"])

        if len(subcategories.intersection(top20_categories)) > 1:
            categories_dist1.add(category)
            continue

        #taking super-categories dist-max = 1
        supercategories = set()
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""SELECT distinct ?superCategoryLabel WHERE
              {{
              <http://dbpedia.org/resource/Category:{}> skos:broader ?superCategory.
              ?superCategory rdfs:label ?superCategoryLabel
              }}
              """.format(category.replace(u'\u200e', '').replace(" ","_")))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            for result in results["results"]["bindings"]:
                if ("stubs" in result["superCategoryLabel"]["value"]):
                    supercategories.add((result["superCategoryLabel"]["value"]).replace("stubs",""))
                elif ("stub" in result["superCategoryLabel"]["value"]):
                    supercategories.add((result["superCategoryLabel"]["value"]).replace("stub",""))
                else:
                    supercategories.add(result["superCategoryLabel"]["value"])

        if len(supercategories.intersection(top20_categories)) > 1:
            categories_dist1.add(category)


    print_coloured_bold("---------------------------", "red")

    percentage_dist1 = len(categories_dist1)/len(official_categories)
    print_coloured_bold("percentage dist1: ", "cyan")
    print(percentage_dist1)

    #second relaxation of requirements
    categories_dist2 = set()
    categories_dist2.update(categories_dist1)
    for category in official_categories.difference(categories_dist1):
        #taking sub-categories dist-max = 2
        subcategories = set()
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""SELECT distinct ?subcategoryLabel WHERE
              {{
              ?subcategory skos:broader?/skos:broader <http://dbpedia.org/resource/Category:{}>.
              ?subcategory rdfs:label ?subcategoryLabel
              }}
              """.format(category.replace(u'\u200e', '').replace(" ","_")))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            for result in results["results"]["bindings"]:
                if ("stubs" in result["subcategoryLabel"]["value"]):
                    subcategories.add((result["subcategoryLabel"]["value"]).replace("stubs",""))
                elif ("stub" in result["subcategoryLabel"]["value"]):
                    subcategories.add((result["subcategoryLabel"]["value"]).replace("stub",""))
                else:
                    subcategories.add(result["subcategoryLabel"]["value"])

        if len(subcategories.intersection(top20_categories)) > 1:
            categories_dist2.add(category)
            continue

        #taking super-categories dist-max = 1
        supercategories = set()
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""SELECT distinct ?superCategoryLabel WHERE
              {{
              <http://dbpedia.org/resource/Category:{}> skos:broader?/skos:broader ?superCategory.
              ?superCategory rdfs:label ?superCategoryLabel
              }}
              """.format(category.replace(u'\u200e', '').replace(" ","_")))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            for result in results["results"]["bindings"]:
                if ("stubs" in result["superCategoryLabel"]["value"]):
                    supercategories.add((result["superCategoryLabel"]["value"]).replace("stubs",""))
                elif ("stub" in result["superCategoryLabel"]["value"]):
                    supercategories.add((result["superCategoryLabel"]["value"]).replace("stub",""))
                else:
                    supercategories.add(result["superCategoryLabel"]["value"])

        if len(supercategories.intersection(top20_categories)) > 1:
            categories_dist2.add(category)


    print_coloured_bold("---------------------------", "red")

    percentage_dist2 = len(categories_dist2)/len(official_categories)
    print_coloured_bold("percentage dist2: ", "cyan")
    print(percentage_dist2)

    path = os.path.join('./Test/Results', file_result )
    with open(path, "a") as f:
        f.write(filename+"__"+str(percentage_exact_match)+"__"+str(percentage_dist1)+"__"+str(percentage_dist2)+"\n")
    return True


def prepare_test(num_articles):
    articles = write_JSONfile_to_dictionary('articles')
    articles_already_taken = set()
    processed_articles = 0

    file_result = str(time.time()).replace(".","")+".txt"

    while processed_articles < num_articles:
        '''res = requests.get('https://en.wikipedia.org/wiki/Special:Random')
        article_name = unquote(res.url.split('/')[-1]).replace("_"," ")'''

        depth = randint(0,3)
        current_category = wikipedia_categories[processed_articles % 27]
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
              """.format(skos, wikipedia_categories[processed_articles % 27].replace(u'\u200e', '')))
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            subcategories = list()
            for result in results["results"]["bindings"]:
                subcategories.append(result["subcategoryLabel"]["value"])
            if len(subcategories) == 0:
                continue
            current_category = subcategories[randint(0,len(subcategories)-1)]

        req = requests.post("https://en.wikipedia.org/wiki/Special:RandomInCategory", data={'wpcategory': current_category })
        name = req.url.split("/")[-1]
        article_name = unquote(req.url.split("/")[-1]).replace("_", " ")
        if "Category:" in article_name or "Special:RandomInCategory" in article_name:
            continue

        if not article_name in articles and not article_name in articles_already_taken:
            try:
                article_page = wikipedia.page(article_name)
            except wikipedia.exceptions.PageError:
                print("Article not found")
                continue
            except wikipedia.exceptions.DisambiguationError:
                print("Disambiguation found")
                continue

            print_coloured_bold("\n==========" + article_name, "red")
            path = os.path.join('./Test', article_name )
            with open(path, "w") as f:
                f.write(article_page.content)
            if (correct_categories_percentage('./Test', article_name, name, file_result)):
                processed_articles += 1
                articles_already_taken.add(article_name)

def final_test_result(total_num_articles):
    articles = set()
    result_exact_match = dict()
    result_dist1 = dict()
    result_dist2 = dict()
    current_num_articles = 0
    duplicates = 0
    folder = "./Test/Results"
    for filename in os.listdir(folder):
        if (current_num_articles == total_num_articles):
            break
        path = os.path.join(folder, filename)
        with open(path, "r") as f:
            for line in f:
                if (current_num_articles == total_num_articles):
                    break
                article_name = line.split("__")[0]
                percentage_exact_match = line.split("__")[1]
                percentage_dist1 = line.split("__")[2]
                percentage_dist2 = line.split("__")[3]
                if (article_name not in articles):

                    rounded_percentage = round(float(percentage_exact_match),1) * 100
                    if rounded_percentage not in result_exact_match:
                        result_exact_match[rounded_percentage] = 0
                    result_exact_match[rounded_percentage] += 1

                    rounded_percentage_dist1 = round(float(percentage_dist1),1) * 100
                    if rounded_percentage_dist1 not in result_dist1:
                        result_dist1[rounded_percentage_dist1] = 0
                    result_dist1[rounded_percentage_dist1] += 1

                    rounded_percentage_dist2 = round(float(percentage_dist2),1) * 100
                    if rounded_percentage_dist2 not in result_dist2:
                        result_dist2[rounded_percentage_dist2] = 0
                    result_dist2[rounded_percentage_dist2] += 1

                    articles.add(article_name)
                    current_num_articles += 1
                else:
                    duplicates += 1

    if (current_num_articles == total_num_articles):
        print_coloured_bold("\ntotal number of articles reached","cyan")
    print_coloured_bold("\nduplicates: "+ str(duplicates),"cyan")

    for key,value in result_exact_match.items():
        result_exact_match[key] = (value / (total_num_articles - duplicates)) * 100
    for i in range(0,11):
        if i*10 not in result_exact_match:
            result_exact_match[i*10] = 0;
    ordered_result_exact_match = collections.OrderedDict(sorted(result_exact_match.items()))
    print_dictionary(ordered_result_exact_match)
    plt.scatter(list(ordered_result_exact_match.keys()),list(ordered_result_exact_match.values()))
    plt.plot(list(ordered_result_exact_match.keys()),list(ordered_result_exact_match.values()), color='r', marker='s', label='Exact match')

    print_coloured_bold("---------------------------------","cyan")

    for key,value in result_dist1.items():
        result_dist1[key] = (value / (total_num_articles - duplicates)) * 100
    for i in range(0,11):
        if i*10 not in result_dist1:
            result_dist1[i*10] = 0;
    ordered_result_dist1 = collections.OrderedDict(sorted(result_dist1.items()))
    print_dictionary(ordered_result_dist1)
    plt.scatter(list(ordered_result_dist1.keys()),list(ordered_result_dist1.values()))
    plt.plot(list(ordered_result_dist1.keys()),list(ordered_result_dist1.values()), color='g', marker='^', label='Dist1')

    print_coloured_bold("---------------------------------","cyan")

    for key,value in result_dist2.items():
        result_dist2[key] = (value / (total_num_articles - duplicates)) * 100
    for i in range(0,11):
        if i*10 not in result_dist2:
            result_dist2[i*10] = 0;
    ordered_result_dist2 = collections.OrderedDict(sorted(result_dist2.items()))
    print_dictionary(ordered_result_dist2)
    plt.scatter(list(ordered_result_dist2.keys()),list(ordered_result_dist2.values()))
    plt.plot(list(ordered_result_dist2.keys()),list(ordered_result_dist2.values()), color='b', marker='o', label='Dist2')


    plt.xlabel("Min number of covered categories (%)")
    plt.ylabel("Number of documents (%)")
    plt.legend(loc='best')
    plt.xlim(left=10)
    plt.show()

#prepare_test(27)
final_test_result(421+1408)
