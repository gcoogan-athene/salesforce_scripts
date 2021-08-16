import codecs
import sfdc

MAIN_MENU_TEXT="""
Dump the Name, ID and Last Run Date of Salesforce Reports based on 
one of the following search options.
Please select one of the following options:
 1. Folder name
 2. Reports NOT executed in last N days
 3. Reports executed in last N days

Enter the search criterion [1-3]: """
SEARCH_BY_FOLDER = 1
SEARCH_BY_NOT_RUN = 2
SEARCH_BY_RUN = 3
RESULTS_OUTPUT_FILE = 'reports.txt'
REPORT_IDS_OUTPUT_FILE = 'report_ids.txt'

def save_to_file(filename, lines):
	""" Save to file """
	with codecs.open(filename, 'wb', 'utf-16') as output_file:
		output_file.write('\r\n'.join(lines))

def dump_reports(soql):
	""" Dumps Salesforce report details given a SOQL """
	sf = sfdc.SFDC('sfdc.yaml')
	if not sf.connected:
		print ("[ERROR]: No connection to Salesforce")
		return False

	# Get list to exclude
	exclude_list = []
	# exclude_str = sf.get_folder_exclude_list()
	# if exclude_str:
	# 	exclude_list = exclude_str.split(',')
	exclude_list = ['Discovery Data Reports',
					'Legal Archive',
					'Athene Admin Reports',
					'Campaign Admin Reports',
					'MFA',
					'Qualtrics Reports']

	# Get terms to exclude
	exclude_terms_list = []
	# exclude_terms_str = sf.get_folder_exclude_terms()
	# if exclude_terms_str:
	# 	exclude_terms_list = exclude_terms_str.split(',')
	exclude_terms_list = [
		'ABRT',
		'SIU',
		'Campaign Admin',
		'Athene Admin',
		'Mass Action']

	results = sf.run_soql(soql)
	if not results or not results.get('totalSize', 0):
		print ("[INFO]: No reports matching search criterion")
		return False

	print ("[INFO]: %d reports matched" % results.get('totalSize'))
	report_ids = []
	lines = []
	for record in results.get('records'):
		folder_name = record.get('FolderName')
		report_name = record.get('Name')
		if exclude_list and folder_name in exclude_list:
			print('Skipping [',report_name,'] due to Folder Name -',folder_name)
		elif exclude_terms_list and [ele for ele in exclude_terms_list if(ele in folder_name)]:
			print('Skipping [',report_name,'] due to term found in Folder Name -',folder_name)
		else:
			line = "%s,%s,%s,%s" % (record.get('Id'),
									folder_name, 
									report_name, 
									record.get('LastRunDate'))
			lines.append(line)
			report_ids.append(record.get('Id'))

	save_to_file(RESULTS_OUTPUT_FILE, lines)
	save_to_file(REPORT_IDS_OUTPUT_FILE, report_ids)
	print ("[INFO]: Full results: %s, Report IDs: %s"
		   % (RESULTS_OUTPUT_FILE, REPORT_IDS_OUTPUT_FILE))
	return True

def main():
	criteria = int(input(MAIN_MENU_TEXT))
	if criteria == SEARCH_BY_FOLDER:
		folder_name = input("Enter folder name: ")
		print ("[INFO]: Searching for reports in folder %s" % folder_name)
		soql = ("SELECT Id, Name, FolderName, LastRunDate FROM Report "
				"WHERE IsDeleted = FALSE AND "
				"FolderName = '%s'" % folder_name)
	elif criteria == SEARCH_BY_NOT_RUN:
		ndays = int(input("Enter number of days: "))
		print ("[INFO]: Searching for reports that were NOT "
			   "executed in the last %d days" % ndays)
		# if report was never executed, the LastRunDate will be null
		soql = ("SELECT Id, Name, FolderName, LastRunDate FROM Report "
				"WHERE IsDeleted = FALSE AND "
				"((LastRunDate = null) OR "
				"(LastRunDate < LAST_N_DAYS:%d))" % ndays)
	elif criteria == SEARCH_BY_RUN:
		ndays = int(input("Enter number of days: "))
		print ("[INFO]: Searching for reports that were "
			   "executed in the last %d days" % ndays)
		soql = ("SELECT Id, Name, FolderName, LastRunDate FROM Report "
				"WHERE IsDeleted = FALSE AND "
				"LastRunDate >= LAST_N_DAYS:%d" % ndays)
	else:
		print ("Invalid search option.")
		return

	dump_reports(soql)

if __name__ == "__main__":
	sf = sfdc.SFDC('sfdc.yaml')
	main()