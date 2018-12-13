import time
import asana
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import secret

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

creds = ServiceAccountCredentials.from_json_keyfile_name(secret.GOOGLE_TOKEN,
                                                         scope)
gc = gspread.authorize(creds)

# get the Bugs sheet, delete and recreate it if it exists
gsheet = gc.open('BugDump')
try:
    bug_sheet = gsheet.worksheet("Bugs")
    gsheet.del_worksheet(bug_sheet)
    gsheet.add_worksheet(title="Bugs", rows=500, cols=5)
except gspread.exceptions.WorksheetNotFound:
    gsheet.add_worksheet(title="Bugs", rows=500, cols=5)
bug_sheet = gsheet.worksheet("Bugs")



# connect to Asana and get the Bugs project id
client = asana.Client.access_token(secret.ASANA_TOKEN)
workspace = list(client.workspaces.find_all())[2]
projects = client.projects.find_all({'workspace': workspace['id']})
bugs_id = [x for x in list(projects) if x['name'] == 'Bugs'][0]['id']

# get the Bugs tasks from Asana
bug_tasks = client.tasks.find_all({'project': bugs_id})
bug_tasks = list(bug_tasks)

# look through the bug tasks and pull out the data
tasks = []
for task in bug_tasks:
    t = client.tasks.find_by_id(task['id'])
    for custom_field in t['custom_fields']:
        name = custom_field['name']
        if name in ['Priority', 'Status', 'Version']:
            enum_value = custom_field['enum_value']
            if enum_value is not None:
                t[name] = enum_value.get('name', '')
            else:
                t[name] = ''
    data = [t['name'], t['Status'], t['completed'], t['Priority'], t['Version']]
    tasks.append(data)


# put the data into the gsheet
header = ['Bug Summary', 'Status', 'Complete', 'Priority', 'Version']
bug_sheet.insert_row(header)
for task in tasks:
    bug_sheet.append_row(task)
    # slow it down so we don't hit the google api write limit
    time.sleep(1.01)
