import json
import argparse
import sfdc
import sys

def move_reports(input_file_name, folder_name):
	""" Moves Salesforce Reports to a folder """
	sf = sfdc.SFDC('sfdc.yaml')
	if not sf.connected:
		print("[ERROR]: No connection to Salesforce")
		return False

	soql = "SELECT Id FROM Folder WHERE Name='%s'" % folder_name
	results = sf.run_soql(soql)
	# We only expect one result as folder name is unique
	if not results or results.get('totalSize', -1) != 1:
		print("[ERROR]: Cannot find folder %s" % folder_name)
		return False

	record = results.get('records')[0]
	folder_id = record.get('Id')
	print("[INFO]: Folder %s, ID: %s" % (folder_name, folder_id))

	with open(input_file_name, 'r',encoding='utf-16') as input_file:
		report_ids = filter(None, input_file.read().splitlines())

	with open(input_file_name, 'r',encoding='utf-16') as input_file2:
		report_ids_2 = filter(None, input_file2.read().splitlines())

	my_len = len([x for x in report_ids_2])

	print("[INFO]: Moving %d reports" % (my_len))
	params = json.dumps({
		"reportMetadata": {
			"folderId": folder_id
		}})
	failed_reports = 0
	for report_id in report_ids:
		resp = sf.update_analytics_api(report_id, params)
		if resp is not None and resp.status_code != 200:
			try:
				json_resp = json.loads(resp.text)
				reason = json_resp[0].get('errorCode', 'N/A')
			except:
				reason = 'N/A'
			print("[FAILED]: Report %s, Reason: %s" % (report_id, reason))
			failed_reports += 1

	print ("[DONE] Failed to move %d reports out of %d" % (failed_reports, my_len))

if __name__ == "__main__":
	cli_parser = argparse.ArgumentParser(description="Mass Reports Mover")
	cli_parser.add_argument('-f',
							'--folder',
							help='Folder name',
							required=True)
	cli_parser.add_argument('-i',
							'--input_file',
							help='File containing Reports ID',
							required=True)
	args = cli_parser.parse_args()
	# All options are required
	if any(v is None for v in vars(args).values()):
		cli_parser.print_help()
		sys.exit(1)

	move_reports(args.input_file, args.folder)