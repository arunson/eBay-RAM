from django.http import HttpResponse
from django.shortcuts import render_to_response
from cs130.eram.forms import SearchForm
import json, urllib
    
def search(request):
	if 'q' in request.GET and request.GET['q']:
		query = urllib.quote(request.GET['q'])
		api_site = "http://svcs.ebay.com/services/search/FindingService/v1"
		version = "1.9.0" 
		app_id = "YOUR ID HERE" 
		global_id = "EBAY-US"
		response_format = "JSON"
		num_responses = "20"

		apiurl = api_site + "?"
		apiurl += "OPERATION-NAME=findItemsByKeywords"
		apiurl += "&SERVICE-VERSION=" + version
		apiurl += "&SECURITY-APPNAME=" + app_id
		apiurl += "&RESPONSE-DATA-FORMAT=" + response_format
		apiurl += "&GLOBAL-ID=" + global_id
		apiurl += "&keywords=" + query
		apiurl += "&paginationInput.entriesPerPage=" + num_responses
		fd = urllib.urlopen(apiurl)
		string_response = fd.read()
		json_response = json.loads(string_response)
		result = "Results: <p>"
		for i in json_response["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"] :
			result += i["title"][0] + "<p>"
		fd.close()	
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

