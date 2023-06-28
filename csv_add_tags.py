#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import exit
import signal

def sigterm_handler(_signo, _stack_frame):
	print("\n")
	file_out.close()
	exit(0)

signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)


def is_cloudflare(ips, tags):
	cloudflare = [
		('103.21.244.1','103.21.247.254'),
		('103.22.200.1','103.22.203.254'),
		('103.31.4.1','103.31.7.254'),
		('104.16.0.1','104.23.255.254'),
		('104.24.0.1','104.27.255.254'),
		('108.162.192.1','108.162.255.254'),
		('131.0.72.1','131.0.75.254'),
		('141.101.64.1','141.101.127.254'),
		('162.158.0.1','162.159.255.254'),
		('172.64.0.1','172.71.255.254'),
		('173.245.48.1','173.245.63.254'),
		('188.114.96.1','188.114.111.254'),
		('190.93.240.1','190.93.255.254'),
		('197.234.240.1','197.234.243.254'),
		('198.41.128.1','198.41.255.254'),
	]
	for ip in ips.split(','):
		for r in cloudflare:
			if r[0] < ip < r[1]:
				tags.append('cloudflare')
				break
	return tags

def is_google(ips, tags):
	google = [
		('64.18.0.0','64.18.15.255'),
		('64.233.160.0','64.233.191.255'),
		('66.102.0.0','66.102.15.255'),
		('66.249.64.0','66.249.95.255'),
		('72.14.192.0','72.14.255.255'),
		('74.125.0.0','74.125.255.255'),
		('108.177.8.0','108.177.15.255'),
		('172.217.0.0','172.217.31.255'),
		('173.194.0.0','173.194.255.255'),
		('207.126.144.0','207.126.159.255'),
		('209.85.128.0','209.85.255.255'),
		('216.239.32.0','216.239.63.255'),
		('216.58.192.0','216.58.223.255'),
	]
	for ip in ips.split(','):
		for r in google:
			if r[0] < ip < r[1]:
				tags.append('google')
				break
	return tags

def is_authority(ips, tags):
	authority_us = [
		'151.201.135.114', # fbi
	]
	for ip in authority_us:
		if ip in ips:
			tags.append('authority_us')
			break
	authority_fr = [
		'77.159.252.152', # FR
		'90.85.16.52', # (FR terrorisme),
		'90.85.16.51', # (FR pédophilie)
		'90.85.16.50' # (FR le reste, non spécifié).
	]
	for ip in authority_fr:
		if ip in ips:
			tags.append('authority_fr')
			break
	return tags

# def is_same_range(line, tags):
# 	TODO


file_out = open('domains_data_tags.csv', 'w')
file_out.write("id;domain;fdn;adguard;orange;sfr;free;status;tags\n")
file_out.flush()
with open('domains_data.csv', 'r') as reader:
	line = reader.readline()#skip header
	line = reader.readline()
	while line != '':
		dom_id, domain, fdn, adguard, orange, sfr, free = line[:-1].split(';')
		if int(dom_id)%100 == 0:
			print(f"{dom_id}/10000000\r", end='')
			file_out.flush()

		status = "NULL"
		tags = []
		if fdn==adguard and adguard==orange and orange==sfr and sfr==free:
			status = 'same_ip' # same IP

		# if ....
		#	status = 'similar_ip' # same IP range

		if fdn!=adguard or adguard!=orange or orange!=sfr or sfr!=free or free!=fdn:
			status = 'diff_ip' # not same IP

		if fdn=='127.0.0.1' or adguard=='127.0.0.1' or orange=='127.0.0.1' or sfr=='127.0.0.1' or free=='127.0.0.1':
			tags.append('localhost')

			if fdn=='127.0.0.1' and adguard=='127.0.0.1' and orange=='127.0.0.1' and sfr=='127.0.0.1' and free=='127.0.0.1':
				tags.append('dead')
			else:
				tags.append('anomaly')

		if fdn=='NoAnswer' or adguard=='NoAnswer' or orange=='NoAnswer' or sfr=='NoAnswer' or free=='NoAnswer':
			tags.append('NoAnswer')

			if fdn=='NoAnswer' and adguard=='NoAnswer' and orange=='NoAnswer' and sfr=='NoAnswer' and free=='NoAnswer':
				if 'dead' not in tags:
					tags.append('dead')
			else:
				tags.append('anomaly')

		for p in [fdn, adguard, orange, sfr, free]:
			tags = is_cloudflare(p, tags)
			tags = is_google(p, tags)
			tags = is_authority(p, tags)
		

		tags = list(set(tags))
		file_out.write(f"{dom_id};{domain};{fdn};{adguard};{orange};{sfr};{free};{status};{','.join(tags)}\n")
		line = reader.readline()

file_out.close()
