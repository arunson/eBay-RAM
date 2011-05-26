from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from cs130.eram.forms import SearchForm
from cs130.eram.other_modules import ebay_module, ipinfo_module
from cs130.eram.review_modules import review_module, productwiki_module, bestbuy_module, ebay_review_module
from cs130.eram import utils
from operator import itemgetter # for sorting items

import os
import datetime
# ip-location
import urllib
import json
import ConfigParser
from django.utils import simplejson

def search(request):
    """
    # For dynamically importing modules #

    mod_list = import_modules(os.getcwd() + '/eram/review_modules')
    mod_path = 'cs130.eram.review_modules.'

    for mod in mod_list :
        mod_name = mod[0]
        mod_class = mod[1]
        exec 'import ' + mod_path + mod_name
    """
    config_path = os.getcwd() + '/eram/module_config.cfg'
		
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(config_path)
        item_ids = ebay_communicator.search(request.GET['q'], 10)

        # This list will be passed to results.html
        item_list = []
        
        # Create list of review modules
        module_list = []
        module_list.append(productwiki_module.ProductwikiInterface(config_path))
        module_list.append(bestbuy_module.BestbuyInterface(config_path))
        ebay_reviewer = ebay_review_module.EbayReviewInterface(config_path)
        
        for item_id in item_ids :
            item_info = ebay_communicator.get_item_info_by_id(item_id)

            # Templates cannot handle variable names with leading @ or _
            item_info["sellingStatus"]["currentPrice"]["value"] = item_info["sellingStatus"]["currentPrice"]["__value__"]
            item_info["sellingStatus"]["currentPrice"]["currencyId"] = item_info["sellingStatus"]["currentPrice"]["@currencyId"]
            
            # Run the title through a filter
            title = item_info["title"]            
            blacklist = ["used", "new", "as-is", "asis", "shipping"]
            title = utils.filter(title, blacklist)
            
            # TODO: filter results with the word "broken"
            #       keep a cache of results for the same query
            # Problem: can't handle input with a star (causes a key error) u\2605
            
            # Query each review module for this item
            search_mode = "slow"
            search_term = title
            item_scores = []
            
            # Try to get the EPID
            try:
                product_id_type = item_info['productId']['@type']
            except KeyError:
                product_id_type = None
            
            if product_id_type == "ReferenceID":
                epid = item_info['productId']['__value__']
                item_scores.append(ebay_reviewer.get_score(epid, "epid"))
            else:
                item_scores.append((-1, -1))
            
            for review_module in module_list:
                (score, number_reviews, query) = query_review_module_by_title(review_module, search_term, search_mode)
                item_scores.append((score, number_reviews))
                
                # Change search mode if necessary
                if (score != -1 or number_reviews != -1):
                    search_mode = "quick"
                    search_term = query
                else:
                    search_mode = "slow"
                    search_term = title

            item_info['score'] = compute_weighted_mean(item_scores)
            item_info['individual_scores'] = item_scores
            
            # Assign colors to scores
            if item_info['score'] >= 66:
                item_info['score_color'] = "high-score"
            elif item_info['score'] >= 33:
                item_info['score_color'] = "med-score"
            else:
                item_info['score_color'] = "low-score"
            
            item_list.append(item_info)
            
        # Sort the item list by score
        item_list = sorted(item_list, key=itemgetter('score'), reverse=True)
        
        # Convert -1s to N/A (if only there was a faster way than another linear pass...)
        for item in item_list:
            if item['score'] == -1:
                item['score'] = "N/A"
        
        # Create a dictionary of variables to pass to the Django template
        template_variables = dict()
        template_variables['search_query'] = request.GET['q']
        template_variables['item_list'] = item_list
        template_variables['location_info'] = get_location(request)

        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form
   
        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})

def jquery_test(request):
    return render_to_response('jquery_test.html')
        
def ip_location(request):
    #ip = request.META['REMOTE_ADDR']
#    url = "http://api.ipinfodb.com/v3/ip-city/?key=" + api_key + "&ip=" + ip + "&format=json"
    
    config = ConfigParser.ConfigParser()
    config.read(os.getcwd() + '/eram/module_config.cfg')
    
    api_key = config.get('LOCATION API', 'api_key')
    
    url = "http://api.ipinfodb.com/v3/ip-city/?key=" + api_key + "&format=json"
    
    ipdb_response = urllib.urlopen(url)

    location_info = json.loads(ipdb_response.read())

    search_form = SearchForm()['q']
    template_variables = dict()
    template_variables['search_form'] = search_form
    template_variables['location_info'] = location_info
    
    
    #my_ip = location_info["ipAddress"]
    #country = location_info["countryName"]
    #region = location_info["regionName"]
    #city = location_info["cityName"]
    #zip = location_info["zipCode"]
    #latitude = location_info["latitude"]
    #longitute = location_info["longitude"]
    #time_zone = location_info["timeZone"]
    
    return render_to_response('ip_location.html', template_variables)

def map_view(request):
    
    config = ConfigParser.ConfigParser()
    config.read(os.getcwd() + '/eram/module_config.cfg')
    config_path = os.getcwd() + '/eram/module_config.cfg'
	
    api_key = config.get('LOCATION API', 'api_key')
    
    url = "http://api.ipinfodb.com/v3/ip-city/?key=" + api_key + "&format=json"
    
    ipdb_response = urllib.urlopen(url)

    location_info = json.loads(ipdb_response.read())

    search_form = SearchForm()['q']
    template_variables = dict()
    template_variables['search_form'] = search_form
    template_variables['location_info'] = location_info
    
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(config_path)
        item_ids = ebay_communicator.search(request.GET['q'], 20)

        # This list will be passed to results.html
        item_list = []

        scores = []
        for item_id in item_ids :
            item_info = ebay_communicator.get_item_info_by_id(item_id)

            # Templates cannot handle variable names with leading @ or _
            item_info["sellingStatus"]["currentPrice"]["value"] = item_info["sellingStatus"]["currentPrice"]["__value__"]
            item_info["sellingStatus"]["currentPrice"]["currencyId"] = item_info["sellingStatus"]["currentPrice"]["@currencyId"]

            #item_info["sellingStatus"]["currentPrice"] = datetime.datetime.strptime(item_info["sellingStatus"]["timeLeft"], "P%dDT%HH%MM%SS")

            item_list.append(item_info)
            # this code is super slow (needs to be parallelized) and is currently useless (returns a list of product score,
            # review number tuples from every module for every item in a pretty bad order).  It's just here to demonstrate how 
            # modules work and needs to be refactored and whatnot
            #for mod in mod_list :
                #exec "mod_communicator = " + mod_path + mod_name + "." + mod_class + "(\'" + config_path + "\')"
                #(score, number_reviews) = mod_communicator.get_score(item_info["title"])
                #scores.append((score, number_reviews))
				
        template_variables['search_query'] = request.GET['q']
        json_list = simplejson.dumps(item_list)
        template_variables['json_list'] = json_list
        template_variables['item_list'] = item_list
       
        return render_to_response('map_view.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})

# Returns a dictionary with location info of user
def get_location(request):
    config = ConfigParser.ConfigParser()
    config.read(os.getcwd() + '/eram/module_config.cfg')
    
    api_key = config.get('LOCATION API', 'api_key')
    
    url = "http://api.ipinfodb.com/v3/ip-city/?key=" + api_key + "&format=json"
    
    ipdb_response = urllib.urlopen(url)

    return json.loads(ipdb_response.read())
    
# convert_module_to_class(name)
# input: name of modules (eg productwiki_module)
# output: name of corresponding class (eg ProductwikiInterface)
# reason: need to be able to tell the name of a module's interface class
# based off the name of the module being dynamically imported
# ---not thoroughly tested---
# ---could be refactored, etc--- 
def convert_module_to_class(name):
	class_name = name[0].upper()
	for i in range(1,name.find('module')-1):
		if name[i] == "_":
			class_name += name[i+1].upper()
		elif name[i-1] != "_":
			class_name += name[i]
	class_name += 'Interface'
	return class_name
			
			
# import_modules(path)
# input: directory containing review modules
# output: dictionary with each key being a module name and each value being the
# corresponding class name
# reason: need to be able to dynamically load modules from the review_modules folder
# to keep minimum coupling between the view and the modules
# ---not thoroughly tested---
# ---could be refactored, etc--- 
def import_modules(path) :
    module_dictionary = [] 
    for i in os.listdir(path) :
        if i[-3:] == '.py':
            mod_name = i[:-3] 
            print mod_name
            if mod_name != 'review_module' and mod_name != '__init__':
                module_dictionary.append((mod_name, convert_module_to_class(mod_name)))

    return module_dictionary

def compute_weighted_mean(score_and_review_list) :
    weighted_sum = 0
    total_weights = 0
    for (score, review_count) in score_and_review_list :
        if (score != -1) :
            weighted_sum += int(score) * int(review_count)
            total_weights += int(review_count)
    if total_weights == 0 :
        return -1
    else :
        return weighted_sum / total_weights


# Returns the score, number of reviews, and last used query        
def query_review_module_by_title(review_module, title, mode) :
    # In quick mode, do not attempt to guess what query would work.
    if mode == "quick":
        number_of_tries = 1
    else:
        number_of_tries = 3
    
    print "\nSearch Mode: " + mode
    
    # This is getting redundant
    number_of_words = 4
    while (number_of_tries > 0) :
        query = utils.get_first_n_words(title, number_of_words)
        print "\nSearch Term: " + query
        (score, reviews_count) = review_module.get_score(query, "title")
        number_of_tries -= 1
        number_of_words -= 1
        if ( score != -1 or reviews_count != -1 ):
            break
            
    return (score, reviews_count, query)
