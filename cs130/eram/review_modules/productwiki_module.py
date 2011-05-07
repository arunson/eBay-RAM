import json, urllib, ConfigParser
import review_module
class ProductwikiInterface:
	def __init__(self, config_location):
		config = ConfigParser.ConfigParser()
		config.read(config_location)
		# caller must handle incorrect configuration location
		self.api_site = config.get('PRODUCTWIKI API', 'api_site')
		self.api_key = config.get('PRODUCTWIKI API', 'api_key')
		self.response_format = config.get('PRODUCTWIKI API', 'response_format')
			
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
		item_list = json_response["products"]	
		first_product = item_list[0]

		return (first_product["proscore"], first_product["number_of_reviews"])
	
