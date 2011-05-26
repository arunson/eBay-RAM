import json, urllib, ConfigParser
import urllib2
import socket # For timeouts

class EbayInterface:
    # __init__(self, config_location)
    # input: location of configuration file
    def __init__(self, config_location):
        config = ConfigParser.ConfigParser()
        config.read(config_location)
        # caller must handle incorrect configuration location
        self.api_site = config.get('EBAY API', 'api_site')
        self.version = config.get('EBAY API', 'version')
        self.app_id = config.get('EBAY API', 'api_key')
        self.global_id = config.get('EBAY API', 'global_id')
        self.response_format = config.get('EBAY API', 'response_format')
            
    # __unlist(self, data)
    # input: data in json format returned by ebay api call
    # output: same data, all lists of 1 length changed to the containing item
    # reason: without it, there is a need to use [0] a lot when trying
    # to access ebay information
    # ---not tested thoroughly---
    def __unlist(self, data):
        if (isinstance(data, list) and (len(data) == 1)):
            return self.__unlist(data[0])
        elif (isinstance(data, dict)):
            for i in data.keys():
                data[i] = self.__unlist(data[i])
            return data
        elif isinstance(data, (list, tuple, set, frozenset)):
            return type(data)(map(self.__unlist, data))
        else:
            return data
        
    # search(self, request, num_responses)
    # input: search term, max number of responses that should be returned by ebay
    # output: list of item ids for each item returned by the api call
    # ---not robust---
    # ---could do with refactoring, etc---
    def search(self, request, num_responses):
        query = urllib.quote(request)
    
        apiurl = self.api_site + "?"
        apiurl += "OPERATION-NAME=findItemsByKeywords"
        apiurl += "&SERVICE-VERSION=" + self.version
        apiurl += "&SECURITY-APPNAME=" + self.app_id
        apiurl += "&RESPONSE-DATA-FORMAT=" + self.response_format
        apiurl += "&GLOBAL-ID=" + self.global_id
        apiurl += "&keywords=" + query
        apiurl += "&paginationInput.entriesPerPage=" + str(num_responses)
        #print apiurl + "\n"

        # a lot of errors that could come up here, have to deal with them at some point
        try:
            fd = urllib2.urlopen(apiurl, timeout = 5)
        except urllib2.URLError, e:
            # We can return some error value if the connection times out
            if isinstance(e.reason, socket.timeout):
                return []
        
        string_response = fd.read()
        fd.close()    

        json_response = json.loads(string_response)
        #print json_response
        response = json_response["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]
        id_list = []
        self.item_dict = {}    
        #print response 
        for i in response :
            item_id = i["itemId"][0]
            self.item_dict[item_id] = i
            del self.item_dict[item_id]["itemId"]
            id_list.append(item_id)
        self.__unlist(self.item_dict)
            
        return id_list 
    
    
    # globalId
    # title
    # country
    # shippingInfo
        # expeditedShipping
        # handlingTime
        # shippingServiceCost
        # oneDayShippingAvaiilable
        # shipToLocations
        # shippingType
    # galleryURL
    # autoPay
    # location
    # postalCode
    # returnsAccepted
    # viewItemURL
    # sellingStatus
        # currentPrice
            # @currencyId
            # __value__
        # timeLeft
        # convertedCurrentPrice
            # @currencyId
            # __value__
        # sellingState
    # paymentMethod
    # primaryCategory
        # categoryID
        # categoryName
    # condition
        # conditionID
        # conditionDisplayName
    # listingInfo
        # listingType
        # gift
        # bestOfferEnabled
        # startTime
        # buyItNowAvailable
        # endTime
    
    # get_item_info_by_id(self, item_id)
    # input: item id previously returned by ebay's api via search
    # output: json formatted information for that item
    # reason: access to ebay information
    # ---could do with refactoring, etc---
    def get_item_info_by_id(self, item_id) :
        return self.item_dict[item_id]


    # Experimental method for eBay's Trading API
    # def get_item_details(self, product_id, config_path):
        # import urllib2
        # config = ConfigParser.ConfigParser()
        # config.read(config_path)
        
        # dev_id = config.get("EBAY TRADING API", "dev_id")
        # app_id = config.get("EBAY TRADING API", "app_id")
        # cert_id = config.get("EBAY TRADING API", "cert_id")
        # user_token = config.get("EBAY TRADING API", "token")
        
        # server_url = "https://api.ebay.com/ws/api.dll"
        
        # site_id = "0"
        
        # api_method = "GetProducts"
        
        # api_level = "721"
        
        ## Construct the headeres needed for the HTTP request
        # http_headers = {"X-EBAY-API-COMPATIBILITY-LEVEL": api_level,    
                        # "X-EBAY-API-DEV-NAME": dev_id,
                        # "X-EBAY-API-APP-NAME": app_id,
                        # "X-EBAY-API-CERT-NAME": cert_id,
                        # "X-EBAY-API-CALL-NAME": api_method,
                        # "X-EBAY-API-SITEID": site_id,
                        # "X-EBAY-API-DETAIL-LEVEL": "0",
                        # "Content-Type": "text/xml"}
        # xml_request = "<?xml version='1.0' encoding='UTF-8?>" + \
                      # "<GetProductsRequest xmlns='urn:ebay:apis:eBLBaseComponents'>" + \
                      # "<ErrorLanguage>en_US</ErrorLanguage>" + \
                      # "<DetailLevel>ReturnAll</DetailLevel>" + \
                      # "<ProductSearch><ProductReferenceID>" + product_id + "</ProductReferenceID></ProductSearch>" + \
                      # "<WarningLevel>High</WarningLevel>" + \
                      # "<RequesterCredentials><eBayAuthToken>" + user_token + "</eBayAuthToken></RequesterCredentials>" + \
                      # "</GetProductsRequest>"
        
        # xml_dict = { "value": xml_request }
        
        # req = urllib2.Request(server_url, xml_request, http_headers)
        # assert req.get_method() == 'POST'
        # response = urllib2.urlopen(req)

        # return response
