import json, urllib, ConfigParser
import review_module
class ProductwikiInterface:
	# __init__(self, config_location)
	# input: location of configuration file
	def __init__(self, config_location):
		config = ConfigParser.ConfigParser()
		config.read(config_location)
		# caller must handle incorrect configuration location
		self.api_site = config.get('PRODUCTWIKI API', 'api_site')
		self.api_key = config.get('PRODUCTWIKI API', 'api_key')
		self.response_format = config.get('PRODUCTWIKI API', 'response_format')
			
	# get_score(self, query)
	# input: query to productwiki
	# output: tuple containing total score (below 100) and number of reviews
	# ---not thoroughly tested---
	# ---not robust---
	def get_score(self, query):
		url_query = urllib.quote(query)
	
		apiurl = self.api_site + "?"
		apiurl += "op=search"
		apiurl += "&q=" + url_query 
		apiurl += "&format=" + self.response_format
		apiurl += "&key=" + self.api_key
		print apiurl
		# a lot of errors that could come up here, have to deal with them at some point
		
		fd = urllib.urlopen(apiurl)
		string_response = fd.read()
		fd.close()	

		json_response = json.loads(string_response)
		first_product = {}
		if ("products" in json_response and json_response["products"] != None ):
			item_list = json_response["products"]	
			first_product = item_list[0]
		else:
			first_product["proscore"] = -1
			first_product["number_of_reviews"] = -1

		return (first_product["proscore"], first_product["number_of_reviews"])
	
