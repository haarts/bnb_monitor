from bs4 import BeautifulSoup
import datetime
import json
import datetime
import urllib.request
import re
import csv
import subprocess


# stupid thing is souper slow when using native request
def get(url, fname):
	f = open(fname, "w")
	subprocess.run(["curl", "--location", "--silent", url], stdout=f)

def extract_bnb_info(raw_bnb):
	# print(raw_bnb)
	bnb = {}
	bnb['link'] = "https://www.bedandbreakfast.nl"+raw_bnb['href']
	# rooms = raw_bnb.find("div", class_="bb_rechts").find("div", string = re.compile("Kamers")).string
	# bnb['rooms'] = int(rooms.replace(" Kamers", ""))
	return bnb


def one_page(url):
	print(url)
	req = urllib.request.Request(url)
	req.add_header('User-Agent', 'prive crawler (Python3, urllib), harm@mindshards.com')
	with urllib.request.urlopen(req) as response:
		return extract_bnbs(response)


def extract_bnbs(content):
	html = content.read()
	soup = BeautifulSoup(html,'html.parser')

	# find bnbs
	bnbs = soup.find('div', class_='first_results').find_all("a")
	# this list contains #review links too
	clean = [href for href in bnbs if re.search("review|detail_map", href['href']) == None]

	bnbs = [extract_bnb_info(bnb) for bnb in clean]
	return bnbs


# main function to get all BNBs in an area, used only once.
def online_bnbs():
	# bnbURL = "https://www.bedandbreakfast.nl/bed-and-breakfast-nl/utrecht/provincie/nederland/2745909"
	bnbURL = "https://www.bedandbreakfast.nl/bed-and-breakfast-nl/utrecht/nederland/c2745912"

	req = urllib.request.Request(bnbURL)
	req.add_header('User-Agent', 'prive crawler (Python3, urllib), harm@mindshards.com')
	req.add_header('Accept', "*/*")
	with urllib.request.urlopen(req) as response:
		html = response.read()
		soup = BeautifulSoup(html,'html.parser')

		# find the pagination item, subtract 2 for the begin and end arrow
		pages = len(soup.find('div', class_='pageNrContainer').find_all("span")) -2
		hrefs = [bnbURL + "?pagenr="+ str(page+1) for page in range(pages)]

		bnbs = [one_page(href) for href in hrefs]
		print("bnbs:")
		print(bnbs)
		flattened = [item for sublist in bnbs for item in sublist]
		print("flattened:")
		print(flattened)
		with open('bnbs.csv', 'w', newline='') as csvfile:
			fieldnames = ['link']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for bnb in flattened:
				writer.writerow(bnb)

def from_file_bnbs():
	bnbs = []
	for x in range(1,7):
		f = open(str(x) + ".html", "r")
		bnbs.extend(extract_bnbs(f))
		
	with open('bnbs.csv', 'w', newline='') as csvfile:
		fieldnames = ['link', 'rooms']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		for bnb in bnbs:
			writer.writerow(bnb)

def get_calendar_data():
	with open('clean_bnbs.csv', newline='') as f:
		lines = f.readlines()
		for line in lines:
			id = re.search("(\d+)\/$", line.rstrip()).group(1)
			url = "https://www.bedandbreakfast.nl/getdataforcalendar?id="+id+"&new=1&year1=2015&month1=11&year2=2016&month2=11"
			get(url, id)
			rate = occupancy_rate(id)
			f = open("rates/"+ id + ".csv", "a")
			f.write(datetime.date.today().strftime("%d-%m-%Y") + ", " + str(rate) + "\n")
			f.close()

def occupancy_rate(id):
	today = datetime.date.today()
	year = str(today.year)
	month = str(today.month)
	day = today.day

	cal_data = json.loads(open(id, "r").read())
	rooms = len(cal_data["m"])

	print(id)
	print(cal_data)

	if isinstance(cal_data["d"][year][month], list):
		return 0.0

	# "u" == unavailable
	if "u" in cal_data["d"][year][month] and day in cal_data["d"][year][month]["u"]:
		return 1.0
	
	# if it does not have this dict key it's fully available
	if not "d" in cal_data["d"][year][month]:
		return 0.0

	# "d" == partial availability
	if str(day) in cal_data["d"][year][month]["d"]:
		return len(cal_data["d"][year][month]["d"][str(day)]) / rooms

	return 0.0

# print(occupancy_rate("4470"))
get_calendar_data()
#from_file_bnbs()
# online_bnbs()

