#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from os import path

con = sqlite3.connect("domains_A.db")
cur = con.cursor()
con.execute("PRAGMA journal_mode=WAL;")
con.execute("CREATE TABLE IF NOT EXISTS domains(id INTEGER PRIMARY KEY, domain VARCHAR UNIQUE, modif_date DATETIME,status INTEGER,fdn TEXT,adguard TEXT,orange TEXT,sfr TEXT,free TEXT,bouygues TEXT,tags TEXT)")
con.commit()

with open('top10milliondomains.csv', 'r') as reader:
	line = reader.readline()#skip header
	line = reader.readline()
	i=0
	while line != '':
		i += 1
		l = line.split('","')
		domain = l[1]
		cur.execute(f"INSERT OR IGNORE INTO domains ('domain') VALUES ('{domain}')")
		if i % 200 == 0:
			con.commit()
		line = reader.readline()
con.commit()