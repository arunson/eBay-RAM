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
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(os.getcwd() + '/eram/module_config.cfg')
        item_ids = ebay_communicator.search(request.GET['q'], 20)

        # This list will be passed to results.html
        item_list = []

        for item_id in item_ids :
            item_info = ebay_communicator.get_item_info_by_id(item_id)

            # Templates cannot handle variable names with leading @ or _
            item_info["sellingStatus"]["currentPrice"]["value"] = item_info["sellingStatus"]["currentPrice"]["__value__"]
            item_info["sellingStatus"]["currentPrice"]["currencyId"] = item_info["sellingStatus"]["currentPrice"]["@currencyId"]

            #item_info["sellingStatus"]["currentPrice"] = datetime.datetime.strptime(item_info["sellingStatus"]["timeLeft"], "P%dDT%HH%MM%SS")

            item_list.append(item_info)

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
