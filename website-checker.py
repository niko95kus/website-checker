#!/usr/bin/python

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from lxml.html import fromstring
import csv
import traceback

import signal
import time
import sys

def exit_gracefully(signum, frame):
	# restore the original signal handler as otherwise evil things will happen
	# in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
	signal.signal(signal.SIGINT, original_sigint)

	try:
		if raw_input("\nReally quit? (y/n)> ").lower().startswith('y'):
			# writeCSV()
			sys.exit(1)

	except KeyboardInterrupt:
		print("Ok ok, quitting")
		sys.exit(1)

	# restore the exit gracefully handler here    
	signal.signal(signal.SIGINT, exit_gracefully)

def checkHTTPS(url):
	r = requests.get('https://' + url, verify=False)
	getData(url, r, True)

def getData(url, r, checkedHttps = False):
	global protocol,redirect,server,title,rc,rcHistory,wordpress,error

	try:
		rc = str(r.status_code)
		rcHistory = str(r.history)
		lastUrl = r.url

		if 'Server' in r.headers:
			server = r.headers['Server']
		else:
			server = ''

		# check wordpress
		if 'wordpress' in r.content.lower() or 'wp-content' in r.content.lower():
			wordpress = 'yes'
		else:
			wordpress = 'no'

		# get title
		tree = fromstring(r.content)
		title = tree.findtext('.//title')
		title = title.encode('utf-8').strip()

		# cek kalo redirect ke HTTPS
		if 'https://' in lastUrl:
			if 'Response [30' in rcHistory: # kalo https karena redirect berarti bisa HTTP and HTTPS
				protocol = 'http,https'
			else: # kalo https bukan karena redirect, berarti cuma bisa HTTPS doang
				protocol += ',https'
		elif not checkedHttps: # tes https kalo blom pernah di cek HTTPS
			print 'checking HTTPS with no redirect'
			protocol = 'http'

			try:
				checkHTTPS(url)
			except Exception as e:
				error = 'ERROR HTTPS:' + str(e)
				print error

		# cek kalo dari HTTP redirect ke HTTPS
		if 'Response [30' in rcHistory:
			redirect = 'redirect'
		else:
			redirect = 'no redirect'
	except Exception as e:
		error = 'ERROR getData:' + str(e)
		print error

# detect CTRL+C
original_sigint = signal.getsignal(signal.SIGINT)
signal.signal(signal.SIGINT, exit_gracefully)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
    'Content-Type': 'text/html',
}

# f = open('contoh.txt', 'r')
f = open('contoh.txt', 'r')
lines = f.readlines()
totalWebsite = len(lines)
f.close()

col = 8
row = totalWebsite

i = 0

with open('tes.csv', mode='wb') as webFile:
	# global protocol,redirect,server,title,rc,rcHistory,wordpress,error
	protocol = redirect = server = title = rc = rcHistory = wordpress = error = ''

	arr = [None] * col

	fieldnames = ['URL', 'HTTP/HTTPS', 'Redirect', 'HTTP_code', 'Error', 'Server', 'Title', 'Wordpress']
	
	writer = csv.writer(webFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	
	writer.writerow(fieldnames)

	for line in lines:
		print 'Processing {} of {}'.format((i+1), totalWebsite)

		try:
			url = line.rstrip()
			print 'URL:' + url

			arr[0] = url

			r = requests.get('http://' + url)
			getData(url, r)

			arr[1] = protocol
			arr[2] = redirect
			arr[3] = rc
			arr[5] = server
			arr[6] = title
			arr[7] = wordpress

			if error:
				print 'print error'
			else:
				print 'Protocol:' + protocol
				print 'Redirect:' + redirect
				print 'Server:' + server
				print 'Title:' + title
				print 'Last Status code:' + rc
				print 'Status history:' + rcHistory
				print 'Is wordpress:' + wordpress

		except TypeError as e:
			error = 'ERROR no website. please double check. ORIGINAL ERROR:' + str(e)
			print error
		except UnicodeEncodeError as e:
			error = 'ERROR UnicodeEncodeError. please double check. ORIGINAL ERROR:' + str(e)
			print error
		except Exception as e:
			error = 'ERROR HTTP:' + str(e)
			print error

			# tes HTTPS
			try:
				print 'checking HTTPS because can\'t connect with HTTP'
				checkHTTPS(url)
			except Exception as e:
				error += '. error HTTPS:' + str(e)
				print error
		finally:
			arr[4] = error

			try:
				writer.writerow(arr)
			except Exception as e:
				arr[1] = arr[2] = arr[3] = arr[5] = arr[6] = arr[7] = ''
				arr[4] = 'Please check manual. ERROR write csv:' + str(e) + arr[4]

				writer.writerow(arr)				

			i += 1

			# deleting local variable and array value
			protocol = redirect = server = title = rc = rcHistory = wordpress = error = ''
			arr[1] = arr[2] = arr[3] = arr[4] = arr[5] = arr[6] = arr[7] = ''

			print ''

