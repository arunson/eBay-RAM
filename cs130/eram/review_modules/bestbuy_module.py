import json, urllib, ConfigParser, urllib2
import review_module
import time
class BestbuyInterface(review_module.ReviewModule):
    supported_types = ["upc", "title"]
    # __init__(self, config_location)
    # input: location of configuration file
    def __init__(self, config_location):
        config = ConfigParser.ConfigParser()
        config.read(config_location)
        # caller must handle incorrect configuration location
        self.api_site = config.get('BESTBUY API', 'api_site')
        self.api_key = config.get('BESTBUY API', 'api_key')
        self.response_format = config.get('BESTBUY API', 'response_format')
        self.call_limit_per_second = float(config.get('BESTBUY API', 'call_limit_per_second'))
        self.name = "Best Buy"

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
        string_response = self.safe_search(api_url)
        try:
            json_response = json.loads(string_response)
        except ValueError:
            return (-1, -1)
        first_product = {}
        if ("products" in json_response and json_response["products"] != None and json_response["products"] != []):
            item_list = json_response["products"]	
            first_product = item_list[0]
        else:
            first_product["customerReviewAverage"] = -1
            first_product["customerReviewCount"] = -1

        return (self.normalize_score(first_product["customerReviewAverage"]), self.normalize_reviews(first_product["customerReviewCount"]))

    """
    def get_score_by_product(self, query, query_type) :
        url_query = urllib.quote(query)
        api_url = self.api_site + "("
        api_url += query_type + "=" query + ")"
        api_url += "?apiKey=" + self.api_key
        api_url += "&format=" + self.response_format
        print urllib.quote(api_url)
        return self.get_score_by_url(urllib.quote(api_url))
    """
    def get_score_by_search(self, query) :
        url_query = query
        api_url = self.api_site
        api_url += urllib.quote("(search=" + url_query + ")")
        api_url += "?apiKey=" + self.api_key
        api_url += "&format=" + self.response_format
        #print api_url
        return self.get_score_by_url(api_url)
        
    def normalize_score(self, score) :
        if score == None or score == -1 :
            return -1
        else :
            return (score / 5) * 100
    def normalize_reviews(self, review_count) :
        if review_count == None :
            review_count = 0
        return review_count
    def safe_search(self, api_url) :
        time.sleep(1. / self.call_limit_per_second)
        try:
            fd = urllib2.urlopen(api_url, timeout = 5)
        except urllib2.URLError, e:
            #if isinstance(e.reason, socket.timeout):
            print self.name + " request timed out"
            #fd.close()
            return (-1, -1)
        string_response = fd.read()
        fd.close()
        return string_response
