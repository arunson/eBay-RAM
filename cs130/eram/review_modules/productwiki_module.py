import json, urllib, ConfigParser
import review_module
class ProductwikiInterface(review_module.ReviewModule):
    supported_types = ["upc", "mpn", "title"]
    # __init__(self, config_location)
    # input: location of configuration file
    def __init__(self, config_location):
        config = ConfigParser.ConfigParser()
        config.read(config_location)
        # caller must handle incorrect configuration location
        self.api_site = config.get('PRODUCTWIKI API', 'api_site')
        self.api_key = config.get('PRODUCTWIKI API', 'api_key')
        self.response_format = config.get('PRODUCTWIKI API', 'response_format')
        self.name = "ProductWiki"

    def get_name(self):
        return self.name

    # get_score(self, query)
    # input: query to productwiki
    # output: tuple containing total score (below 100) and number of reviews
    # ---not thoroughly tested---
    # ---not robust---
    def get_score(self, query, query_type):
        if (query_type not in self.supported_types) :
            return (-1, -1)
        if (query_type == "title") :
            return self.get_score_by_search(query)
        if (query_type == "upc" or query_type == "mpn") :
            return self.get_score_by_product(query, query_type)

    def get_score_by_url(self, api_url) :
        fd = urllib.urlopen(api_url)
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


    def get_score_by_product(self, query, query_type) :
        url_query = urllib.quote(query)
        api_url = self.api_site + "?"
        api_url += "op=product"
        api_url += "&format=" + self.response_format
        api_url += "&idtype=" + query_type
        api_url += "&idvalue=" + url_query
        api_url += "&key=" + self.api_key
        return self.get_score_by_url(api_url)

    def get_score_by_search(self, query) :
        url_query = urllib.quote(query)
        api_url = self.api_site + "?"
        api_url += "op=search"
        api_url += "&q=" + url_query 
        api_url += "&format=" + self.response_format
        api_url += "&key=" + self.api_key
        return self.get_score_by_url(api_url)
		
