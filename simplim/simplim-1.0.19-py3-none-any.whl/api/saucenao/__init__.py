r"""@2020 HARDRELICE. All Rights Reserved.
 ╻ ╻ ┏━┓ ┏━┓ ┏━┓ ┏━┓ ┏━╸ ╻   ╻  ┏━╸ ┏━╸ TM
 ┣━┫ ┣━┫ ┣━┛ ┃ ┃ ┣━┛ ┣━╸ ┃   ┃  ┃   ┣━╸
 ╹ ╹ ╹ ╹ ╹ ╹ ┗━┛ ╹ ╹ ┗━╸ ┗━╸ ╹  ┗━╸ ┗━╸

A tool using website <https://saucenao.com/> & its search method <https://saucenao.com/search.php/> to search & match anime pics
"""

import requests as rq
from bs4 import BeautifulSoup as bs

test_image = 'https://i.pximg.net/c/240x480/img-master/img/2022/02/24/00/00/10/96477280_p0_master1200.jpg'
link = 'https://saucenao.com/search.php?url='
#url = 'http://c2cpicdw.qpic.cn/offpic_new/2733937760/122527455-3725687086-E6B4900521AB2A7FCC0B848E4D45212E/0'

def search(url,number):
	# headers={
	# 	'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
	# 	'Cookie': '_ga=GA1.2.1836370903.1648539949; _gid=GA1.2.1853205226.1648539949; _pbjs_userid_consent_data=3524755945110770; __gads=ID=5babfb0803796dc1:T=1648539972:S=ALNI_Ma5CJMhXzPaCCtv1Tvi125669kx9g; _im_vid=01FZAA7E0K221XX365EFE8H0PT; _im_uid.3929=i.yXxarQkhR1W1OlOqX_Nrtg; cto_bundle=U3Uza19kN2w2ZWFGYkhHS3Q0dWVPYmtlaXp4djEyU0dZbUw0VGhkbnJHS0FNb0l6V3lFNWNiY05JYjk0ZFo0T2hiMU1XdjhvajU1VlA3SjRabWczWUwyeUVQOGduSiUyRnc3WWREbDdqcVhWSGZNNmdwOTNiJTJCTDdNcWVzN09nTG5hcFhTRkdBalRLWFZMZDJPUTVVblRleVdaQzBqT0tkZ0UlMkJ1eTdqeTZjdTVEc3NJcWdOODM4S1NEcXltcmhSZSUyRkZ5V3RkOQ; cto_bidid=m8n1Cl8lMkZGJTJGZkpIdEhZekhrdSUyRlU5dUQxOEVXd3lqJTJGVGFqNjRCRzNZVkhPQUpzNlA0Zkt1QkE1UVpYb1BSU2klMkZ3QkE0aDN6Q09sM0RIcnlzZnJlZFllQkVLVkhpU2M3VWtyckY4MFc5amZ0WHBORDBHa1hwTUo5bmI1Z2hOUkVvUFo3S09mb1Nza29iMFhzeGcwSiUyQlFDYkJ5dGclM0QlM0Q'
	# }
	page = rq.get(link+url).text
	page = bs(page,'lxml')
	results = page.find_all(class_ = 'result') 
	if len(results)==0:
		return -1
	if results[0].get('id')=='result-hidden-notification':
		results = page.find_all(class_ = 'result hidden')
	package = []
	for result in results[:number]:
		similarity_str = result.find(class_='resultsimilarityinfo').text
		similarity = float(similarity_str[:-1])
		thumbnail = result.find(class_='resultimage').find('img').get('src')
		title = result.find(class_='resulttitle').text
		print(thumbnail)
		content = result.find(class_='resultcontentcolumn')
		site = 'None'
		if content.find('strong'):
			site = content.find('strong').text
		TV = 'None'
		ID = 'None'
		ID_link = 'None'
		author = 'None'
		author_link = 'None'
		if site=='None':
			pass
		elif site=='Title: ':
			site = 'None'
			TV = content.text
		else:
			site=site[:-5]
			info = content.find_all(class_='linkify')
			if len(info)!=0:
				try:
					ID = info[0].text
					ID_link = info[0].get('href')
				except:
					ID = ''
					ID_link = ''
				try:
					author = info[1].text
					author_link = info[1].get('href')
				except:
					author = ''
					author_link = ''
		pack={'similarity_str':similarity_str, 'similarity':similarity, 'thumbnail':thumbnail, 'title':title, 'site':site,'TV':TV, 'ID':ID, 'author':author, 'ID_link':ID_link, 'author_link':author_link}
		package.append(pack)
	return package