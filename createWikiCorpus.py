from utils import *
import os
import json

# creating data structures
stems = dict()
stemmed_titles = dict()
articles = dict()
categories = dict()

def add_article_to_dictionaries(article_name, normalized_redirections, categories_list):
    #category dictionary
    for category in categories_list:
        if not category in categories:
            categories[category] = {"num_articles": 1, "vocabulary": set()}
        else:
            categories[category]["num_articles"] += 1

    for redirection in normalized_redirections:
        if(len(redirection)>1):
            #stems dictionary
            words = redirection.split()
            for word in words:
                if not word in stems:
                    stems[word] = set()
                stems[word].add(redirection)
                for category in categories_list:
                    categories[category]["vocabulary"].add(word)
            #stemmed_titles dictionary
            if not redirection in stemmed_titles:
                stemmed_titles[redirection] = set()
            stemmed_titles[redirection].add(article_name)

    #articles dictionary
    articles[article_name] = categories_list


def create_final_dataset(total_num_articles):
    current_num_articles = 0
    duplicates = 0
    folder = "./ArticlesToMerge"
    for filename in os.listdir(folder):
        if (current_num_articles == total_num_articles):
            break
        path = os.path.join(folder, filename)
        with open(path, "r") as f:
            num_articles = int(f.readline())
            read_articles_in_file = 0
            while (read_articles_in_file < num_articles):
                if (current_num_articles == total_num_articles):
                    break
                article_name = f.readline().strip()
                normalized_redirections = eval(f.readline().strip())
                categories_list = eval(f.readline().strip())
                if (article_name not in articles):
                    add_article_to_dictionaries(article_name, normalized_redirections, categories_list)
                    current_num_articles += 1
                else:
                    duplicates += 1
                read_articles_in_file += 1

    if (current_num_articles == total_num_articles):
        print_coloured_bold("\ntotal number of articles reached","cyan")
    print_coloured_bold("\nduplicates: "+ str(duplicates),"cyan")
    print_coloured_bold("\ntotal number articles: "+ str(total_num_articles-duplicates),"cyan")

    #remove categories with less than 1 article
    categories_to_remove = list()
    for key,value in categories.items():
        if value["num_articles"] < 5:
            categories_to_remove.append(key)

    for category in categories_to_remove:
        del categories[category]

    for key,value in articles.items():
        articles[key]=value.difference(categories_to_remove)

    #save dictionaries to files
    write_dictionary_to_JSONfile(stems,"stems")
    write_dictionary_to_JSONfile(stemmed_titles,"stemmed_titles")
    write_dictionary_to_JSONfile(articles,"articles")
    write_dictionary_to_JSONfile(categories,"categories")

create_final_dataset(50233)

