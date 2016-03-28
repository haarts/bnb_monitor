from bs4 import BeautifulSoup
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
	#print(raw_bnb)
	bnb = {}
	bnb['link'] = "https://www.bedandbreakfast.nl"+raw_bnb.find("a")['href']
	rooms = raw_bnb.find("div", class_="bb_rechts").find("div", string = re.compile("Kamers")).string
	bnb['rooms'] = int(rooms.replace(" Kamers", ""))
	return bnb


def one_page(url):
	print(url)
	req = urllib.request.Request("https://www.bedandbreakfast.nl"+url)
	req.add_header('User-Agent', 'prive crawler (Python3, urllib), harm@mindshards.com')
	with urllib.request.urlopen(req) as response:
		return extract_bnbs(response)


def extract_bnbs(content):
	html = content.read()
	soup = BeautifulSoup(html,'html.parser')

	# find bnbs
	bnbs = soup.find('div', id='resultaten').find_all("div", recursive=False)[1:-1]
	bnbs = [extract_bnb_info(bnb) for bnb in bnbs]
	return bnbs


def online_bnbs():
	# bnbURL = "https://www.bedandbreakfast.nl/bed-and-breakfast-nl/utrecht/provincie/nederland/2745909"
	bnbURL = "https://www.bedandbreakfast.nl/bed-and-breakfast-nl/utrecht/nederland/c2745912"

	req = urllib.request.Request(bnbURL)
	req.add_header('User-Agent', 'prive crawler (Python3, urllib), harm@mindshards.com')
	req.add_header('Accept', "*/*")
	with urllib.request.urlopen(req) as response:
		html = response.read()
		soup = BeautifulSoup(html,'html.parser')

		# find the pagination item
		pages = soup.find('div', id='resultaten').find_all("div", recursive=False)[-1].find_all("a")
		hrefs = [page['href'] for page in pages]

		bnbs = [one_page(href) for href in hrefs[0:-1]]
		flattened = [item for sublist in bnbs for item in sublist]
		with open('bnbs.csv', 'w', newline='') as csvfile:
			fieldnames = ['link', 'rooms']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for bnb in bnbs:
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
	with open('bnbs.csv', newline='') as csvfile:
		import datetime
		spamreader = csv.reader(csvfile)
		for row in spamreader:
			id = re.search("(\d+)\/$", row[0]).group(1)
			rooms = row[1]
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

#print(occupancy_rate("9786"))
# get_calendar_data()
#from_file_bnbs()
list_all_bnbs()


