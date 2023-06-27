#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
python3 check_domain.py -s orange -r A -d domains_A.db
python3 check_domain.py -s fdn -r A -d domains_A.db
python3 check_domain.py -s adguard -r A -d domains_A.db
"""


# sudo apt install python3-psycopg2 python3-dnspython
# or
# pip3 install dnspython
# pip3 install psycopg2
from dns.resolver import Resolver
from argparse import ArgumentParser
from sys import exit
import sqlite3
import psycopg2
from os import path
import time
import threading
import signal

USE_SQLITE_DB = False
MAX_THREAD = 20
BATCH_SIZE = 100000

# If you use postgresql
PG_HOST="<change me!>"
PG_USER="<change me!>"
PG_PASSWORD="<change me!>"
PG_PORT="5432"

nameservers = {
	"fdn":{
		'A':['80.67.169.12', '80.67.169.40'],
		'AAAA':['2001:910:800::12', '2001:910:800::40']
	},
	"adguard":{
		'A':['94.140.14.140', '94.140.14.141'],
		'AAAA':['2a10:50c0::1:ff', '2a10:50c0::2:ff']
	},
	"orange":{
		'A':['192.168.1.1']
	},
	"free":{
		'A':['192.168.0.254']
	},
	"sfr":{
		'A':['192.168.1.1'] # 109.0.66.10 109.0.66.20
	}
}
ns_list = []
for n in nameservers:
    ns_list.append(n)

parser = ArgumentParser()
parser.add_argument('-s', '--ns', help=f"Nameserver [{'|'.join(ns_list)}] (default='fdn')", default='fdn')
parser.add_argument('-r', '--rdatatype', help="rdatatype [A|AAAA] (default='A')", default='A')
parser.add_argument('-d', '--db', help="Sqlite3 database name (default='domains_A.db')", default='domains_A.db')
args = parser.parse_args()

nameserver = args.ns
if not nameserver in nameservers:
	print(f"Nameserver not valide!")
	exit(0)

rdatatype = args.rdatatype
if not rdatatype in ['A', 'AAAA']:
	print(f"rdatatype not valide!")
	exit(0)

db_name = args.db
if USE_SQLITE_DB and not path.isfile(db_name) :
	print(f"The database file doesn't exist!")
	exit(0)


BATCH_FILE_PATH = f"batch_{nameserver}_{rdatatype}.csv"

resolver = Resolver(configure=False)
resolver.nameservers = nameservers[nameserver][rdatatype]

con = None
if USE_SQLITE_DB:
	sql_now = "datetime('now')"
else:
	sql_now = "now()"

def sigterm_handler(_signo, _stack_frame):
	if con != None:
		con.close()
	exit(0)

signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

def thread_resolve(dom_id, nameserver, resolver, qname, rdatatype):
	global sql
	answers = []
	try:
		for answer in resolver.resolve(qname, rdatatype):
			answers.append(str(answer))
	except Exception as e:
		pass
	if answers == []:
		answers = ['NoAnswer']
	else:
		answers.sort()
	sql.append(f"UPDATE domains SET {nameserver}='{','.join(answers)}', modif_date={sql_now} WHERE id={dom_id};")


def thread_save(sql):
	global con
	not_done=True
	if USE_SQLITE_DB:
		con = sqlite3.connect(db_name, timeout=10)
	else:
		con = psycopg2.connect(database="domains",
			host=PG_HOST,
			user=PG_USER,
			password=PG_PASSWORD,
			port=PG_PORT)

	cur = con.cursor()
	while not_done:
		try:
			if USE_SQLITE_DB:
				cur.executescript(sql)
			else:
				cur.execute(sql)
			con.commit()
			not_done = False
		except Exception as e:
			time.sleep(0.1)
	con.close()

batch = []
def make_batch():
	global con
	global batch
	if USE_SQLITE_DB:
		con = sqlite3.connect(db_name, timeout=10)
	else:
		con = psycopg2.connect(database="domains",
			host=PG_HOST,
			user=PG_USER,
			password=PG_PASSWORD,
			port=PG_PORT)
	cur = con.cursor()
	limit = 10000
	print("Build batch...\r", end='')
	not_done=True
	while not_done:
		try:
			result = cur.execute(f"SELECT id, domain FROM domains WHERE {nameserver} IS NULL LIMIT {limit}")
			if USE_SQLITE_DB:
				batch = result.fetchall()
			else:
				batch = cur.fetchall()
			not_done = False
		except Exception as e:
			print('sleep', e)
			time.sleep(0.1)

	con.close()
	print("                    \r", end='')
	return len(batch)


if make_batch() >0:
	result = batch.pop()
	print(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
else:
	result = False

sql=[]
i=0
while result:
	dom_id = result[0]
	qname = result[1]
	while threading.active_count() > MAX_THREAD:
		time.sleep(0.05)

	x = threading.Thread(target=thread_resolve, args=(dom_id, nameserver, resolver, qname, rdatatype,))
	x.start()

	if i%1000 ==0:
		print(f'{i}\r', end='')
		while threading.active_count() > 1:
			# wait thread to finish
			time.sleep(0.05)
		# save
		x = threading.Thread(target=thread_save, args=("\n".join(sql),))
		sql=[]
		x.start()

	i+=1

	try:
		result = batch.pop()
	except Exception as e:
		while threading.active_count() > 1:
			# wait thread to finish
			time.sleep(0.05)
		if make_batch() >0:
			result = batch.pop()
		else:
			result = False
