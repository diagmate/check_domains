# Check domains [POC]

2023-06-16  
A POC to find censored domains and anomalies in France.  
Like [RIPE Atlas](https://atlas.ripe.net/) we use probes (Raspberry-Pi) with various Internet providers.  
We have query top [10 million domains](https://www.domcop.com/top-10-million-domains). It's only a tiny part of Internet.  
  
Actualy we have datas from :  
- Orange  
- SFR  
- Free  
- FDN  
- Adguard  

Need probe for :  
- Bouygues  
  
Result can be found here : https://github.com/diagmate/check_domains_data   

# Install

You can have :  
- many probes and one database server (Postgresql)  
or
- one probe with local database (Postgresql or Sqlite3)  



## For probe
```bash
sudo apt install python3-dnspython
```
If you use postgresql :  
```bash
sudo apt install python3-psycopg2 postgresql-client
```
Else if you use sqlite :  
```bash
sudo apt install sqlite3
```


## For Sqlite3 database
Download top10milliondomains.csv :  
```bash
./get_top_10million_domains.sh
```
DL 118,6Mo

Create database :  
```bash
screen -S chkdomain
# takes many hours !
python3 csv_to_sqlite.py
```
Notes for `screen`:  
Leave screen open : CTRL+a d  
Join screen : `screen -R chkdomain`  
  
In `check_domain.py`, change :  
```
USE_SQLITE_DB = True
```
  
Now you can run check_domain.py :  
```bash
# screen -S chkdomain
# takes 3-4 days to finish !
python3 check_domain.py -s adguard -r A -d domains_A.db
```
`-s` can be : `fdn`, `adguard`, `orange`, `free`, `sfr`  
`-r` can be : `A` or `AAAA`
  
If you want to export the database in csv :  
```bash
# screen -S chkdomain
# long time !
sqlite3 -header -csv domains_A.db "select id, domain, fdn, adguard, orange, sfr, free from domains;" > domains_data.csv
```

Add tags :
```bash
# screen -S chkdomain
# takes many hours !
python3 csv_add_tags.py
```

## For Postgresql database

On the Postgresql server.  
  
### Install Postgresql
Replace `<SERVER_IP>` and `<SERVER_NETWORK>`.  
Example `123.146.178.42` and `123.146.178.0`.  
```bash
sudo apt install postgresql postgresql-client screen
sudo sed -i "s|#listen_addresses = 'localhost'|listen_addresses = 'localhost,<SERVER_IP>'|" /etc/postgresql/13/main/postgresql.conf
echo "host    all             all             <SERVER_NETWORK>/24            md5" |sudo tee -a /etc/postgresql/13/main/pg_hba.conf
sudo sed -i "s|shared_buffers = 128MB|shared_buffers = 512MB|" /etc/postgresql/13/main/postgresql.conf
sudo systemctl restart postgresql
```

### user and DB
```bash
su - postgres
createuser --pwprompt userdns
createdb -O userdns domains
```

From one probe, test the connexion to the database :

```bash
psql -U userdns -d domains -h <SERVER_IP> --pass
```

### Init the database

On the Postgresql server.  

Download top10milliondomains.csv :  
```bash
screen -S chkdomain
./get_top_10million_domains.sh
# DL 118,6Mo
psql -U userdns -d domains -h <SERVER_IP> --pass
```
Notes for `screen`:  
Leave screen open : CTRL+a d  
Join screen : `screen -R chkdomain`  

```sql
DROP TABLE IF EXISTS "domains";
CREATE TABLE "domains"(
	id SERIAL PRIMARY KEY,
	domain VARCHAR UNIQUE,
	modif_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
	status INTEGER,
	fdn TEXT,
	adguard TEXT,
	orange TEXT,
	sfr TEXT,
	free TEXT,
	bouygues TEXT,
	tags TEXT);
create index idx_domains on domains(id);

-- postgresql only
COMMENT ON COLUMN "domains"."status" IS '0: not done, 1: same IP, 2: same IP s range, 3: not same IP';
```

```sql
COPY persons(id, domain) FROM 'top10milliondomains.csv' DELIMITER ',' CSV HEADER;
```

### From probes

In `check_domain.py`, change :
```
USE_SQLITE_DB = False
PG_HOST="<change me!>"
PG_USER="<change me!>"
PG_PASSWORD="<change me!>"
PG_PORT="5432"
```
Then
```bash
screen -S chkdomain
# takes 3-4 days to finish !
python3 check_domain.py -s adguard -r A
```
`-s` can be : `fdn`, `adguard`, `orange`, `free`, `sfr`  
`-r` can be : `A` or `AAAA`

### export and add tags

```bash
screen -S chkdomain
echo "id;domain;fdn;adguard;orange;sfr;free" > domains_data.csv
# takes many hours to finish !
psql -U userdns -d domains -h <SERVER_IP> --pass -P format=unaligned -P tuples_only -P fieldsep=\; -c "SELECT id, domain, fdn, adguard, orange, sfr, free FROM domains order by id" >> domains_data.csv
python3 csv_add_tags.py
```


# Stats of domains_data_tags.csv

Data can be found here : https://github.com/diagmate/check_domains_data   
2023-06-16  

`status` : NULL, same_ip or diff_ip
`tags` : localhost, dead, anomaly, NoAnswer, authority_us, authority_fr, cloudflare, google

```
$ grep same_ip domains_data_tags.csv|wc -l
8620982
$ grep diff_ip domains_data_tags.csv|wc -l
1379018
$ grep localhost domains_data_tags.csv|wc -l
6281
$ grep dead domains_data_tags.csv|wc -l
1112333
$ grep anomaly domains_data_tags.csv|wc -l
2642
$ grep NoAnswer domains_data_tags.csv|wc -l
1224020
$ grep authority_fr domains_data_tags.csv|wc -l
74
$ grep authority_us domains_data_tags.csv|wc -l
155
$ grep cloudflare domains_data_tags.csv|wc -l
813047
$ grep google domains_data_tags.csv|wc -l
137745
$ grep diff_ip domains_data_tags.csv | grep localhost|wc -l
2549
$ grep diff_ip domains_data_tags.csv | grep localhost|grep dead|wc -l
1
$ grep diff_ip domains_data_tags.csv | grep NoAnswer|wc -l
118304
$ grep diff_ip domains_data_tags.csv | grep NoAnswer|grep dead|wc -l
50
$ grep diff_ip domains_data_tags.csv | grep localhost |grep anomaly|grep NoAnswer|wc -l
1495
```
