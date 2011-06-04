from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from cs130.eram.forms import SearchForm
from cs130.eram.other_modules import ebay_module, ipinfo_module
from cs130.eram.review_modules import review_module, productwiki_module, bestbuy_module, ebay_review_module
from cs130.eram import utils
from operator import itemgetter # for sorting items

from review_module_thread import ReviewModuleThread
from item_thread import ItemThread

import os
import datetime
import threading
import time # for sleep()
# ip-location
import urllib
import json
import ConfigParser
from django.utils import simplejson
        
# Sequential version of search
def search(request):
    config_path = os.getcwd() + '/eram/module_config.cfg'
		
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(config_path)
        item_ids = ebay_communicator.search(request.GET['q'], 20)

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
                (score, number_reviews, query) = utils.query_review_module_by_title(review_module, search_term, search_mode)
                item_scores.append((score, number_reviews))
                """
                # Change search mode if necessary
                if (score != -1 or number_reviews != -1):
                    search_mode = "quick"
                    search_term = query
                else:
                    search_mode = "slow"
                    search_term = title
                """
            item_info['score'] = utils.compute_weighted_mean(item_scores)
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
        
        # Needed by the JS code used to display items on Google Maps        
        json_list = simplejson.dumps(item_list)
        template_variables['json_list'] = json_list
        
        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form
   
        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})

# Spawns threads for eBay items
def search_threaded(request):
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
        
        thread_list = []
        for item_id in item_ids:
            item_info = ebay_communicator.get_item_info_by_id(item_id)
            thread_list.append(ItemThread(item_info, ebay_reviewer, module_list))
        
        # Tries to enforce API calls/sec limits, but is not the correct approach.
        # Condition variables and locking schemes are better.
        import time
        for item_thread in thread_list:
            time.sleep(1./5)
            item_thread.start()
        for item_thread in thread_list:
            item_thread.join()
            item_list.append(item_thread.get_item_info())
        
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
        
        json_list = simplejson.dumps(item_list)
        template_variables['json_list'] = json_list

        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form
   
        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})
        
# Spawns threads for review modules
def search_threaded2(request):
    config_path = os.getcwd() + '/eram/module_config.cfg'
		
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(config_path)
        item_ids = ebay_communicator.search(request.GET['q'], 10)


        # This list will be passed to results.html
        item_list = []
        
        # Passed to review modules
        product_ids = []
        product_titles = []
        
        for item_id in item_ids :
            item_info = ebay_communicator.get_item_info_by_id(item_id)

            # Templates cannot handle variable names with leading @ or _
            item_info["sellingStatus"]["currentPrice"]["value"] = item_info["sellingStatus"]["currentPrice"]["__value__"]
            item_info["sellingStatus"]["currentPrice"]["currencyId"] = item_info["sellingStatus"]["currentPrice"]["@currencyId"]
            
            # Run the title through a filter
            title = item_info["title"]            
            blacklist = ["used", "new", "as-is", "asis", "shipping"]
            title = utils.filter(title, blacklist)
            
            product_titles.append(title)
            
            # Try to get the EPID
            try:
                product_id_type = item_info['productId']['@type']
            except KeyError:
                product_id_type = None
            
            # Prepare product_ids[]
            if product_id_type == "ReferenceID":
                epid = item_info['productId']['__value__']
                product_ids.append(epid)
            else:
                product_ids.append("")
                
            item_list.append(item_info)
        
        # Create list of review modules
        module_list = []
        module_list.append(productwiki_module.ProductwikiInterface(config_path))
        module_list.append(bestbuy_module.BestbuyInterface(config_path))
        ebay_reviewer = ebay_review_module.EbayReviewInterface(config_path)
        
        thread_list = []
        
        ebay_thread = ReviewModuleThread(ebay_reviewer, product_ids, "epid", 15)
        thread_list.append(ebay_thread)
        ebay_thread.start()
        
        for module in module_list:
            module_thread = ReviewModuleThread(module, product_titles, "title", 5)
            thread_list.append(module_thread)
            module_thread.start()
        
        scores_list = []
        for module_thread in thread_list:
            module_thread.join()
            scores_list.append(module_thread.get_scores())
        
        # "Invert" the list so that we can take the average scores
        scores_list = zip(*scores_list)

        
        # Average the scores
        averaged_scores = []
        for item_scores, item_info in zip(scores_list, item_list):
            item_info['score'] = utils.compute_weighted_mean(item_scores)
            item_info['individual_scores'] = item_scores
            
            # Assign colors to scores
            try:
                if item_info['score'] >= 66:
                    item_info['score_color'] = "high-score"
                elif item_info['score'] >= 33:
                    item_info['score_color'] = "med-score"
                else:
                    item_info['score_color'] = "low-score"
            except KeyError:
                # If there was no score then it should be "low-score"
                item_info['score_color'] = "low-score"
        
        
        # Sort the item list by score
        item_list = sorted(item_list, key=itemgetter('score'), reverse=True)
        
        # Convert -1s to N/A (if only there was a faster way than another linear pass...)
        for item in item_list:
            try:
                if item['score'] == -1:
                    item['score'] = "N/A"
            except KeyError:
                item['score'] = "N/A"
        
        # Create a dictionary of variables to pass to the Django template
        template_variables = dict()
        template_variables['search_query'] = request.GET['q']
        template_variables['item_list'] = item_list
        
        # Needed by the JS code used to display items on Google Maps
        json_list = simplejson.dumps(item_list)
        template_variables['json_list'] = json_list

        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form
   
        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})

# Just a simple jQuery test. Loads up a page with some jQuery code in it.   
def jquery_test(request):
    return render_to_response('jquery_test.html')
        
def ip_location(request):    
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

            item_list.append(item_info)
				
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
