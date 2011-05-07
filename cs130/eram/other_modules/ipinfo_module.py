import json, urllib, ConfigParser
class IpInfoInterface:
	def __init__(self, config_location):
		config = ConfigParser.ConfigParser()
		config.read(config_location)
		# caller must handle incorrect configuration location
		self.api_site = config.get('IPINFO API', 'api_site')
		self.app_id = config.get('IPINFO API', 'app_id')
		self.response_format = config.get('IPINFO API', 'response_format')
			
	#my_ip = return_value["ipAddress"]
	#country = return_value["countryName"]
	#region = return_value["regionName"]
	#city = return_value["cityName"]
	#zip = return_value["zipCode"]
	#latitude = return_value["latitude"]
	#longitute = return_value["longitude"]
	#time_zone = return_value["timeZone"]
	def get_ip_info(self, request):
		apiurl = self.api_site + "?"
		apiurl += "key=" + self.app_id
		apiurl += "&ip=" + request
		apiurl += "&format=" + self.response_format

		fd = urllib.urlopen(apiurl)
		string_response = fd.read()
		fd.close()	

		json_response = json.loads(string_response)
		return json_response
