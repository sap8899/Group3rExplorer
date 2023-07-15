import re
import csv
import pandas
import plotly.express as px

class Finding:
    def __init__(self, color, reason, details):
        self.color = color
        self.reason = reason
        self.details = details

    def get_str(self):
        out = f"Color: {self.color}\n Reason: {self.reason}\n Details: {self.details}"
        return out.replace("\n" ,"\\n")

class Setting:
    def __init__(self, setting_type, policy_type, content="", finding=None):
        self.setting_type = setting_type
        self.policy_type = policy_type
        self.content = content
        self.finding = finding


class GPO:
    def __init__(self, name, settings):
        self.name = name
        self.settings = settings


    
output_data = []
def parse_content(setting):
    if "___" in setting:
       split_setting = setting.split("___")
       setting = split_setting[0]
    out_str = ""
    fix_setting = setting.replace(" ","")
    setting_text = fix_setting.split("\n")
    for line in setting_text[3:]:
        splited_line = line.split("|")
        if len(splited_line) > 3:
            line_val = splited_line[1]
            line_data = splited_line[2]
            if line_val == "":
                out_str = out_str + f" {line_data} "
            else:
                out_str = out_str + f" {line_val} : {line_data} "
    #print(out_str)
    return out_str.replace("\n","\\n")
        
        


def parse_finding(finding):
    finding_reg = re.compile("\| Finding \|(.*?)\|.*Reason  \|(.*)\| Detail  \|(.*)\|")
    finding_data  = finding_reg.search(finding)
    if finding_data:
         finding_groups = finding_data.groups()
         if len(finding_groups) == 3:
            color = (finding_groups[0]).replace('|', "")
            reason = (finding_groups[1]).replace('|', "")
            details = (finding_groups[2]).replace('|', "")
            finding = Finding(color, reason, details)
            return finding
    return ""
    

def parse_setting(setting):
    setting_pattern = re.compile("\| Setting - (.*)\|")
    setting_data = setting_pattern.search(setting)
    if setting_data:
        setting_groups = setting_data.groups()
        if len(setting_groups) == 1:
            settings_title = setting_groups[0].split('|')
            setting_type = settings_title[0]
            setting_X = settings_title[1]
        else:
            setting_X = ''
            setting_type = ''
    else:
            setting_X = ''
            setting_type = ''

    setting_text = setting.split("\n")
    finding_string = ''
    finding_flag = 0
    for line in setting_text:
        if "| Finding |" in line:
            finding_flag = 1
        if finding_flag == 1 and "| Setting" not in line:
            finding_string = finding_string + line
    finding = parse_finding(finding_string)
    content = parse_content(setting)
    setting_obj = Setting(setting_type, setting_X, content, finding)
    return setting_obj

        

def parse_gpo(gpo):
    # Regular expressions to extract data from the log
    gpo_guid_pattern = re.compile("\| GPO +\| (.*?) +\|\n.*\n\|(.*)\|\n\|(.*)\|\n\|(.*)\|\n\|(.*)\|\n\|(.*)\|\n\|(.*)\|")
        
    gpo_data = gpo_guid_pattern.search(gpo)
    if gpo_data:    
        gpo_groups = gpo_data.groups()
        if len(gpo_groups) == 7:
            name = gpo_groups[0]
        else:
            name = "No name"

    else:
        name = "No name"
    settings_list = []

    gpo_text = gpo.split("\n")
    setting_string = ''
    setting_flag = 0
    for line in gpo_text:
        if "| Setting -" in line:
            setting_flag = 1
        if setting_flag == 1 and line != "\___":
            setting_string = setting_string + f"\n{line}"
        if setting_flag == 1 and line == "\___":
            setting = parse_setting(setting_string)
            settings_list.append(setting)
            setting_flag = 0
            setting_string = ''

    gpo = GPO(name, settings_list)
    return gpo

        
print("Welcome to Group3rExplorer!\n")
grouper_log = input("Enter log path: ")
output_html = input("Enter output path: ")

file1 = open(grouper_log, 'r')
Lines = file1.readlines()


gpo_list = []



gpo_flag = 0
gpo_string = ''
for line in Lines:
    if "[Finish]" in line:
        break
    if "| GPO             |" in line and gpo_flag == 0:
        gpo_flag = 1
    if "[GPO]" not in line and gpo_flag ==1:
        gpo_string = gpo_string + line
    if "[GPO]" in line and gpo_flag == 1:
        gpo_object = parse_gpo(gpo_string)
        gpo_list.append(gpo_object)
        gpo_flag = 0
        gpo_string = ''


for gpo_obj in gpo_list:
    gpo_name = gpo_obj.name
    gpo_settings_list = gpo_obj.settings
    for setting in gpo_settings_list:
        finding = setting.finding
        if finding:
            finding_str = finding.get_str()
        else:
            finding_str = ""
        output_data.append({
        "GPO" : gpo_name,
        "setting_type": f"{setting.setting_type}",
        "policy_type": f"{setting.policy_type}",
        "content": f"{setting.content}",
        "finding": f"{finding_str}"
        })

### Save the data to a CSV file
output_file = "parsed_log.csv"
with open(output_file, "w", newline="") as csv_file:
    fieldnames = ["GPO", "setting_type", "policy_type", "content", "finding"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for row in output_data:
        writer.writerow(row)

print(f"Data has been successfully parsed and saved to {output_file}.")



file = pandas.read_csv("parsed_log.csv", encoding = "utf-8")
a = file.to_html().replace("\\n","<br>")
b = pandas.read_html(a)[0]
b = b.drop('Unnamed: 0', axis=1)
b = b.fillna(value="None")
fig = px.treemap(b, path=[px.Constant("Policies"),'GPO','setting_type', 'policy_type', 'content', 'finding'])
fig.data[0].textinfo = 'label'
fig.update_traces(root_color="lightgrey")
fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
fig.update_layout(font_size=20)
fig.write_html(output_html)
print(f"\nYour Explorer is ready! at {output_html}")
