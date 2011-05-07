from django.http import HttpResponse
from django.shortcuts import render_to_response
from cs130.eram.forms import SearchForm
from cs130.eram.other_modules import ebay_module, ipinfo_module
import os
import datetime
# ip-location
import urllib
import json
import ConfigParser

def search(request):
    mod_list = import_modules(os.getcwd() + '/eram/review_modules')
    mod_path = 'cs130.eram.review_modules.'
    config_path = os.getcwd() + '/eram/module_config.cfg'
    for mod in mod_list :
        mod_name = mod[0]
        mod_class = mod[1]
        exec 'import ' + mod_path + mod_name
		
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
            for mod in mod_list :
                exec "mod_communicator = " + mod_path + mod_name + "." + mod_class + "(\'" + config_path + "\')"  
                (score, number_reviews) = mod_communicator.get_score(item_info["title"])
                scores.append((score, number_reviews))	
				
        template_variables = dict()
        template_variables['search_query'] = request.GET['q']
        template_variables['item_list'] = item_list

        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form

        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})

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
			if mod_name != 'review_module' and mod_name != '__init__':
				module_dictionary.append((mod_name, convert_module_to_class(mod_name)))

	return module_dictionary

