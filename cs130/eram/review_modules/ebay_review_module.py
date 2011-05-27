import json, urllib2, ConfigParser
import review_module

# WARNING: NOT TO BE CONFUSED WITH EBAYINTERFACE IN OTHER_MODULES
class EbayReviewInterface(review_module.ReviewModule):
    supported_types = ["epid"]
    
    def __init__(self, config_location):
        config = ConfigParser.ConfigParser()
        config.read(config_location)
        # caller must handle incorrect configuration location
        self.api_site = config.get('EBAY SHOPPING API', 'api_site')
        self.api_key = config.get('EBAY SHOPPING API', 'api_key')
        self.response_format = config.get('EBAY SHOPPING API', 'response_format')
        self.site_id = config.get('EBAY SHOPPING API', 'site_id')
        self.version = config.get('EBAY SHOPPING API', 'version')
        self.name = "eBay"
    
    def get_name(self):
        return self.name
        
    def get_score(self, query, query_type):
        if (query_type not in self.supported_types):
            return (-1, -1)
        if (query_type == "epid"):
            return self.get_score_by_epid(query)
            
    def get_score_by_epid(self, query):
        api_url = self.api_site 
        api_url += "?callname=FindReviewsAndGuides"
        api_url += "&responseencoding=" + self.response_format
        api_url += "&appid=" + self.api_key
        api_url += "&siteid=" + self.site_id
        api_url += "&ProductID.type=Reference"
        api_url += "&ProductID.Value=" + query
        api_url += "&version=" + self.version
        return self.get_score_by_url(api_url)
        
    # Current assumption: called by get_score_by_epid (meaning unique results)
    def get_score_by_url(self, api_url):
        print api_url
        fd = urllib2.urlopen(api_url)
        string_response = fd.read()
        fd.close()
        
        try:
            json_response = json.loads(string_response)
        except ValueError:
            return (-1, -1)
            
        try:
            if (json_response['ReviewCount'] > 0):
                score = self.normalize_score(json_response['ReviewDetails']['AverageRating'])
                num_reviews = json_response['ReviewCount']
                return (score, num_reviews)
            else:
                return (-1, -1)
        except KeyError:
            return (-1, -1)
        
    def normalize_score(self, score) :
        if score == None or score == -1 :
            return -1
        else :
            return (score / 5) * 100    
    