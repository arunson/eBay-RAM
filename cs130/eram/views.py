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
