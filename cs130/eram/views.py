from django.http import HttpResponse
from django.shortcuts import render_to_response
from cs130.eram.forms import SearchForm
from cs130.eram.other_modules import ebay_module
import os
    
def search(request):
	if 'q' in request.GET and request.GET['q']:
		ebay_communicator = ebay_module.EbayInterface(os.getcwd() + '/eram/module_config.cfg')
		item_ids = ebay_communicator.search(request.GET['q'], 20)
		result = "Results: <p>"
		for item_id in item_ids :
			item_info = ebay_communicator.get_item_info_by_id(item_id)
			try:
				result += "<img src=\"" + item_info["galleryURL"] + "\"\\>"
			except KeyError:
				result += "NO PIC"
			result += "    <a href=\"" + item_info["viewItemURL"] + "\">" + item_info["title"] + "</a>"
			result += "<p>"
		return HttpResponse(result)
	else:
		search_form = SearchForm()
	return render_to_response('search.html', {'search_form': search_form})

def ip_location(request):
    ip = request.META['REMOTE_ADDR']
    api_key = ""
    url = "http://api.ipinfodb.com/v3/ip-city/?key=" + api_key + "&ip=" + ip + "&format=json"

    ipdb_response = urllib.urlopen(url)

    location_info = json.loads(ipdb_response.read())

    #my_ip = location_info["ipAddress"]
    #country = location_info["countryName"]
    #region = location_info["regionName"]
    #city = location_info["cityName"]
    #zip = location_info["zipCode"]
    #latitude = location_info["latitude"]
    #longitute = location_info["longitude"]
    #time_zone = location_info["timeZone"]
    
    return render_to_response('ip_location.html', location_info)
