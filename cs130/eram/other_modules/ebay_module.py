import json, urllib, ConfigParser
class EbayInterface:
	def __init__(self, config_location):
		config = ConfigParser.ConfigParser()
		config.read(config_location)
		# caller must handle incorrect configuration location
		self.api_site = config.get('EBAY API', 'api_site')
		self.version = config.get('EBAY API', 'version')
		self.app_id = config.get('EBAY API', 'app_id')
		self.global_id = config.get('EBAY API', 'global_id')
		self.response_format = config.get('EBAY API', 'response_format')
			
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
		fd = urllib.urlopen(apiurl)
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
	
	"""
	globalId
	title
	country
	shippingInfo
		expeditedShipping
		handlingTime
		shippingServiceCost
		oneDayShippingAvaiilable
		shipToLocations
		shippingType
	galleryURL
	autoPay
	location
	postalCode
	returnsAccepted
	viewItemURL
	sellingStatus
		currentPrice
			@currencyId
			__value__
		timeLeft
		convertedCurrentPrice
			@currencyId
			__value__
		sellingState
	paymentMethod
	primaryCategory
		categoryID
		categoryName
	condition
		conditionID
		conditionDisplayName
	listingInfo
		listingType
		gift
		bestOfferEnabled
		startTime
		buyItNowAvailable
		endTime
	"""
	def get_item_info_by_id(self, item_id) :
		return self.item_dict[item_id]
