import requests
import yaml
import json

from simple_salesforce import Salesforce

DEBUG = True
SFDC_BASE_URL = "https://{0}.salesforce.com"
SFDC_SERVICE_URL = "https://{0}.salesforce.com/services/data/v{1}"

def log_exception(ex_msg):
	if DEBUG:
		print("[EXCEPTION]: %s" % str(ex_msg))

class SFDC(object):
	def __init__(self, config_path):
		self.connected = False
		self._sf = None

		if self._init_session(config_path):
			self._init_endpoints()

	def _init_session(self, config_path):
		""" Read configuration file and establish connection to SFDC """
		try:
			with open(config_path) as f:
				sfdc_config = yaml.load(f,Loader=yaml.SafeLoader)
		except:
			print("[ERROR]: Cannot load config file %s" % config_path)
			return False

		# Username and password must be set in config file
		if 'user' not in sfdc_config or 'password' not in sfdc_config:
		   	print("[ERROR]: Config must contain 'user' and 'password'")
		   	return False

		self._api_version = "50.0"
		token = ''

		temp_list = sfdc_config.split(' ')
		sfdc_config = {}
		sfdc_config['user'] = temp_list[0].split(':')[1]
		sfdc_config['password'] = temp_list[1].split(':')[1]
		sfdc_config['token'] = temp_list[2].split(':')[1]
		sfdc_config['domain'] = temp_list[3].split(':')[1]

		if 'api_version' in sfdc_config:
			self._api_version = str(sfdc_config['api_version'])
		if 'token' in sfdc_config:
			token = str(sfdc_config['token'])

		try:
			session = requests.Session()
			self._sf = Salesforce(username=sfdc_config['user'], 
								  password=sfdc_config['password'],
								  version=self._api_version,
								  security_token=token,
								  session=session,
								  domain=sfdc_config['domain'])
		except Exception as e:
			print("[ERROR]: Cannot connect to SFDC", str(e))
			return False

		self._auth_id = 'Bearer ' + self._sf.session_id
		self._session = self._sf.session
		self.connected = True
		return True

	def _init_endpoints(self):
		""" Initialize SFDC REST API endpoints URLs """
		pod = (self._sf.base_url
				   .replace('https://', '')
				   .split('.salesforce.com')[0])
		self._base_url = SFDC_BASE_URL.format(pod)
		self._service_url = SFDC_SERVICE_URL.format(pod, self._api_version)
		self._tooling_api = self._service_url + '/tooling/query/'

		if DEBUG:
			print("[DEBUG]: Base URL", self._base_url)
			print("[DEBUG]: Service URL", self._service_url)
			print("[DEBUG]: Tooling API", self._tooling_api)

	def _get_headers(self):
		return {'Authorization': self._auth_id}

	def query_tooling_api(self, q):
		""" Query SFDC tooling API """
		try:
			resp = self._session.get(self._tooling_api,
								 	 params={'q': q},
								 	 headers=self._get_headers())
		except Exception as e:
			print("[ERROR]: Query tooling API failed")
			if DEBUG:
				print("[EXCEPTION]: %s" % str(e))
			return None

		try:
			j_resp = json.loads(resp.content)
			return j_resp
		except Exception as e:
			print("[ERROR]: Tooling API response not JSON")
			log_exception(e)
			return None

	def update_tooling_api(self, resource_uri, params):
		""" Update an object using tooling API """
		resource_url = self._base_url + resource_uri
		headers = self._get_headers()
		headers['Content-Type'] = 'application/json'
		try:
			resp = self._session.patch(resource_url, 
									   data=params, 
									   headers=headers)
		except Exception as e:
			print("[ERROR]: Update tooling API failed")
			log_exception(e)
		return resp

	def update_analytics_api(self, resource_id, params):
		""" Update an object using analytics API """
		res_uri = self._service_url + '/analytics/reports/' + resource_id
		headers = self._get_headers()
		headers['Content-Type'] = 'application/json'
		try:
			resp = self._session.request('PATCH', 
									 	 res_uri, 
									 	 headers=headers, 
									 	 data=params)
		except Exception as e:
			print("[ERROR]: Update Analytics API failed")
			log_exception(e)
			return None
		return resp

	def run_soql(self, q):
		""" Runs a SOQL query """
		try:
			result = self._sf.query_all(q)
		except Exception as e:
			print("[ERROR]: run_soql failed")
			log_exception(e)
			return None
		return result