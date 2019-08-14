#!/usr/bin/env python
import sys
import socket
import urllib
import string
import MySQLdb
from datetime import datetime
import time
import os
import signal
import operator
from multiprocessing import Process

from radix_tree import RadixTree, DuplicateKeyError

host = 'localhost'
update_time = int(time.time())-172800 # two days before the execution
download_time=0
th_lag_check = 10000
th_lag = 600

path = "unknown"
source = "unknown"
th_msg = 0.1
sizeth = 512
tokenth = 8
DELIM=" "

filter_process={}
temp_recent = {}
tree_recent={}
th_recent = 1000
th_recent_capacity=100
recent_facility=set()

def signal_handler(signal, frame):
	outf = open("/data/bw/helo/exit.sig","w")
        outf.write('Received signal ' +str(signal) + '\n Exiting program\n')
	outf.close()
        sys.exit(0)

# saves the log messages into a file that will be later bulkloaded later
def bulkload_logs(msg, utime, template_id, facility, location, priority, logtime, system, bootid, pid, process, temp_filter, temp_process):
	#date = datetime.fromtimestamp(int(time_unit)).strftime('%Y%m%d_%H%M')
	if int(temp_filter)==0:
		# write into the msgLog link
		file_name = "./msgLogTest"
		in_f = open(file_name,"a")
		in_f.write(str(source)+"\t"+str(utime)+"\t"+str(logtime)+"\t"+str(facility)+"\t"+str(system)+"\t"+str(location)+"\t"+str(pid)+"\t"+str(bootid)+"\t"+str(priority)+"\t"+str(template_id)+"\t"+string.join(msg," ")+"\t\n")
		in_f.close()

	if int(temp_process)==1:
		# write into the processLog link
		file_name = "./processLogTest"
		in_f = open(file_name,"a")
		in_f.write(str(source)+"\t"+str(utime)+"\t"+str(logtime)+"\t"+str(facility)+"\t"+str(system)+"\t"+str(location)+"\t"+str(pid)+"\t"+str(bootid)+"\t"+str(priority)+"\t"+str(template_id)+"\t0\t"+string.join(msg," ")+"\t\n")
		in_f.close()





# downloads the initial set of templates from the database at iscm
def download_templates(msg_sys):
	# temp_list[system] = RadixTree with the template description as key and template id as value 
	return [temp_list_active, temp_list_inactive];



# updates the template list so that to match the last message
# downloads everything from the update_time (usefull for parallel version
# in case every service node runs independently)
def update_templates(msg, msg_sys, temp_list_active, temp_list_inactive):
	global update_time, source, filter_process
	return (current_temp,temp_list_active,temp_list_inactive)


#searches the two words to see if they have the same hybrid form
def hybrid(msg, temp):
	#print "-",msg,"-",temp,"-"
	if temp[0]=='[' and msg[0]=='[':
		if len(temp)>1 and len(msg)>1:
			return 0
	hybrid = [".", "=", ":", "-", "(", "["]
	for hy in hybrid:
		msg_pos = msg.find(hy,0)
		if msg_pos<1:
			continue
		temp_pos = temp.find(hy,0)
		if temp_pos<1 or temp_pos>=len(temp)-1:
			continue
		#print temp, temp_pos, len(temp)
		if msg[:msg_pos]==temp[:temp_pos] and temp[temp_pos+1]=="*":
			return 0
	#sda to sdy
#	if len(msg)==4 and len(temp)==4:
#		if msg[0:2]=="sd" and temp[0:2]=="sd":
#			return 0
#	if msg[0:3]=="eth" and temp[0:3]=="eth":
#		return 0
	return -1


# gets the first part of a hybrid word 
def get_hybrid(msg):
	msg_final=''
	msg_pos=-1
	hybrid = [".", ",", "=", ":", ";", "-", "+", "(",")","<",">","[","]","@"]
	for hy in hybrid:
		pos = msg.find(hy,0)
		#print hy, pos
		if pos>0 and pos<len(msg)-2:
			if msg_pos==-1 or (msg_pos>pos):
				msg_final = msg[:pos+1]
				msg_pos = pos
	if msg_pos==-1:
		return msg
	return msg_final


#finds a match between the current message and the list of templates
def find_template_match(msg, temp_list, msg_sys):
	global filter_process
	ret = temp_list.HELO_match(string.join(msg," "))
	#print "Match",ret
	#print "Match",ret[0],temp_list.HELO_contains_tempID(ret[0])
	desc = ret[1]
	tempid = ret[0]
	if ret[0]==-1:
		return -1
	#print msg_sys, tempid, msg_sys in filter_process, tempid in filter_process[msg_sys]
	ret2 = filter_process[msg_sys][tempid] 
	return (int(tempid),ret2[0],ret2[1],desc) # return id, filter, process, desc


def test():
	# if the message has only one word we directly look for the template
	if len(msg)==1:
		# get the hybrid word
		wrd = get_hybrid(msg[0])
		print wrd
		tid=set(i for i in temp_list if len(temp_list[i][2])==1 and wrd in temp_list[i][2][0])
		# temp_list has the format: system - template - (filter process message)
		if len(tid)>0:
			taux = tid.pop()
			return (taux, temp_list[taux][1], temp_list[taux][0])
		tid=set(i for i in temp_list if len(temp_list[i][2])==2 and wrd in temp_list[i][2][0] and "n+" in temp_list[i][2])
		# temp_list has the format: system - template - (filter process message)
		if len(tid)>0:
			taux = tid.pop()
			return (taux, temp_list[taux][1], temp_list[taux][0])
		return -1 

	# else we find a list of possible candidates
	tid=set(i for i in temp_list if len(temp_list[i][2])<=len(msg)+1 and len(temp_list[i][2])>=len(msg)/2)
	# parse the message and filter the temp_list based on the words of the messages that are not hybrid or contain numbers
	for pos in range(len(msg)/2):
		if len(tid)<10:
			break
		wrd=msg[pos]
		try:
			wc=int(wrd)
			continue
		except:
			#p=wrd.find("\\",0)
			#if p>0:
			#	continue
			if is_hybrid(wrd):
				continue
		# if the iteration got to this point, wrd represents an english word
		taux=set(i for i in tid if wrd==temp_list[i][2][pos] or temp_list[i][2][pos]=="*" or temp_list[i][2][pos]=="n+")
		tid = set(tid&taux)

	ec_max=0
	tempid_max = 0
        tempp_max = 0
        tempf_max = 0
	for tempid in tid:
		wc=0
		ec=0
		# temp has the format: system - template - (filter process message)
		temp = temp_list[tempid][2] 
		temp_process = temp_list[tempid][1]
		temp_filter = temp_list[tempid][0] 

		for i in range(min(len(msg),len(temp),20)):
			if len(msg[i])<1 and len(temp[i])<1:
				continue
			msg[i] =  msg[i].replace("\\", "")
			if msg[i]==temp[i]:
				ec=ec+2
				continue
			if temp[i]=='*':
				continue
			if temp[i]=='d+':
				continue
			if temp[i]=='n+':
				break
			if hybrid(msg[i], temp[i])==0:
				ec=ec+1
				continue
			wc=-1
			break

	
		if wc==-1:
			continue	
		if len(temp)>len(msg)+1:
			continue
  		if ec>2*len(msg) or 1.*ec/(2.*len(msg))<th_msg:
                        continue

		if ec_max < ec:
			#print ec,temp
			ec_max=ec
			tempid_max = tempid
			tempp_max = temp_process
			tempf_max = temp_filter
		
		#return (tempid, temp_process, temp_filter)
	if tempid_max==0:
		return -1
	else:
		#print (tempid_max, tempp_max, tempf_max)
		return (tempid_max, tempp_max, tempf_max)
	return -1


# transforms time from Blue Waters format to unix timestamp
def time_to_unix(log_time):
	# for abe, transform from Jun  5 04:02:25 to unix timestamp
	date = datetime.strptime("2012 "+log_time, "%Y %b %d %H:%M:%S")
	t = date.timetuple()
	return str(time.mktime(t)).split(".")[0]

#get the system from Blue Waters format (from "system[pid]:" in "system")
def get_system(bw_sys):
	system = bw_sys.split(":")
	if len(system)==1:
		return 'none'
	return system[0].split("[")[0]

# checks if a word is only formed of english letters (return False) or is a hybrid token (return True)
def is_hybrid(msg):
	wrd = ["of","to","on","as"]
	if len(msg)<3:
		if msg not in wrd:
			return True
		else:
			return False

	hybrid = [".", ",", "=", ":", ";", "-", "+", "(",")","<",">","[","]","@"]
	for hy in hybrid:
		msg_pos = msg.find(hy,0)
		if msg_pos>1 and msg_pos<len(msg)-2:
			return True
		
	for i in range(len(msg)):
		try:
			aux = int(msg[i])
			return True
		except:
			continue
	return False

# looks at each words in a message and counts the hybrid words. If this number exceeds the number of non-hybrid words, we classify the message with template id 0 
def lookup_eventtype(msg):
	if len(string.join(msg," "))>sizeth:
		return 1	
	hyb=0
	wrd=0
	for i in msg:
		if is_hybrid(i)==True:
			hyb=hyb+1
			continue
		else:
			wrd=wrd+1

	#print "hybrid",hyb,"normal",wrd
	if hyb>=(3*wrd/2):
		return 1
	else:
		return 0

def activate_template(tempid, facility):
	# move from inactive to active list

def update_recent_list(temp_id, temp_desc, facility):
	global temp_recent, tree_recent
	if facility not in tree_recent:
		tree_recent[facility] = RadixTree()
	ts = int(time.time())

        #print "Tree"
        #print(tree_recent[facility].debug())

	if (temp_id, facility) in temp_recent:
		temp_recent[(temp_id, facility)]=ts
		return
	if tree_recent[facility].HELO_contains_tempID(temp_id)==True:
		return

	temp_recent[(temp_id, facility)]=ts

	#print "Temp recent ",temp_recent," threshold ",th_recent_capacity
	if len(temp_recent)>th_recent_capacity:
		# find the element to delete from the recent list
		sorted_x = sorted(temp_recent.iteritems(), key=operator.itemgetter(1))
		tree_recent[sorted_x[0][0][1]].HELO_delete_tempID(sorted_x[0][0][0])
		del temp_recent[(sorted_x[0][0][0], sorted_x[0][0][1])]
	tree_recent[facility].insert(temp_desc, temp_id)


# analyzes each log message (data) and classifies it or creates a new template depending on the find_template_match function
def analyze_message(temp_list, temp_list_inactive, data, th_update, lag_check, logout):
	global download_time, temp_recent, tree_recent, th_recent, recent_facility

	# get data
	#if len(data)<9:
	#	return 2

	data = data.split("\n")[0].split(DELIM)
	if len(data)<9:
		return 2
	#print data, data[8], data[9]

	facility = 'none'	

	try:
		utime = int(data[0])
        	facility = data[1].lower()
       		priority = data[2]
		logtime = data[3]
		location = data[4]
		system = data[5]
		pid = data[6]
		bootid = data[7]
		msg = data[8:]
	except:
		return 2

      	displayit = 0


	if pid == "-" or pid == "":
		pid="NULL";

	#print data, len(msg)
	msg_init = msg
	#msg = [i.lower() for i in msg]
	msg = [i.lower() for i in msg if i!='']
	if len(msg)<1:
		#print string.join(data," ")
		return 2
	if len(msg)==1:
		try:
			aux = int(msg[0])
			#print string.join(data," ")
			return 2
		except:
			pass

	# find a match
	process=0
	template_id=-1
	temp_filter=0
        temp_process=0

	pos=-1


	#print msg

	# check the recent list of templates first
	if facility in tree_recent and facility in recent_facility:
		pos = find_template_match(msg, tree_recent[facility], facility)
		logout.write("Search in recent templates: "+str(pos)+"\n")
		if pos>-1: # we have a match
			template_id=pos[0]
			temp_process = pos[2]
			temp_filter = pos[1]			
			ts = int(time.time())
			temp_recent[(template_id, facility)] = ts
			pos=-1

	#print facility, facility in temp_list
	if facility in temp_list and template_id==-1:
		pos = find_template_match(msg, temp_list[facility], facility)
		logout.write("Search in active templates: "+str(pos)+"\n")
	if pos!=-1 and template_id==-1:
		#print "Active - Classified in the "+str(pos[0])+" template id"
		template_id = pos[0]
		temp_process = pos[2]
		temp_filter = pos[1]
		# add the recent list
		if facility in recent_facility:
			update_recent_list(template_id, pos[3], facility)
		pos=-1

	if template_id==-1:	
		# check the inactive list
		if facility in temp_list_inactive:
			pos = find_template_match(msg, temp_list_inactive[facility], facility)
		logout.write("Search in inactive templates: "+str(pos)+"\n")
		if pos!=-1:
			#print "Inactive - Classified in the "+str(pos[0])+" template id"
			template_id = pos[0]
			temp_process = pos[2]
			temp_filter = pos[1]
			# activate the template that had a match
			temp_list[facility].insert(pos[3],template_id)
			# add the recent list
			if facility in recent_facility:
				update_recent_list(template_id, pos[3], facility)

			p1 = Process(target=activate_template, args=(template_id,facility))
			p1.start()
			activate_template(template_id, facility)
		else:			
			ret=0
			if facility != 'moab':
				ret = lookup_eventtype(msg)
			if ret==1:
				#print "All hybrid message, classified with template id 0"
				template_id=0
			else:
\				ret = update_templates(msg, facility, temp_list, temp_list_inactive)
				#print ret[0]
				temp_list = ret[1]
				temp_list_inactive = ret[2]
				template_id = ret[0]
				try:
					temp_process = temp_list[facility][template_id][1]
					temp_filter = temp_list[facility][template_id][0]
				except:
					temp_process=0
				#print "Updated with id "+str(ret[0])

	logout.write("Classified with id "+str(template_id)+"\n")
	if template_id!=-1:
		#send_logs(msg, utime, template_id, facility, location, priority, logtime, system, bootid, pid, process)
		bulkload_logs(msg_init, utime, template_id, facility, location, priority, logtime, system, bootid, pid, process, temp_filter, temp_process)
	else:
		#print "Filtered",data
		pass
	
	# check timestamp to determine if it is the time to upload the template list
	#print template_id, utime, facility, system
	#print msg
	if download_time==0:
		download_time = utime
		#print download_time

	if lag_check==1:
		# check if the lag exceeds a threshold
		dif = time.time()-utime
		#print "Time lag",dif
		logout.write("Check timelag "+str(dif)+" download time "+str(utime-download_time)+" threshold "+str(th_update)+"\n");

		if dif>th_lag:
			strtemp = "HELO lag time exceeds the threshold of "+str(th_lag)+" seconds. Current time lag: "+str(dif)+" seconds"
			bulkload_logs(strtemp.split(DELIM), utime, 2, "isc", -1, -1, int(time.time()), -1, -1, -1, 1, 0, 1)

		# check if we need to update the template list
                if utime-download_time> th_update:
                        download_time = utime
                        return -1

	return 1


# the main function - downloads the initial set of templates
# reads from stdin log messages and calls the analysis function
def main():
	# verifing command line arguments
	global source, download_time
	global path, filter_process, th_recent, recent_facility

	start = time.time()
	download_time = int(time.time())
	th_update = 3600
	if len(sys.argv)<2:
		print "Usage: ",sys.argv[0]," source [path] [update_time]"
		return

	source = sys.argv[1]
	path = source
	if len(sys.argv)>2:
		path = sys.argv[2]
	if len(sys.argv)>3:
		th_update = int(sys.argv[3])

	start = time.time()
	ret = download_templates('none')
	temp_list = ret[0]
	#print(temp_list['moab'].debug())

	temp_list_inactive = ret[1] 
	print "Download time:", time.time()-start

	recent_facility = set()
	for i in filter_process:
		if len(filter_process[i])>th_recent:
			recent_facility.add(i)
	print len(recent_facility)
	#for i in temp_list_inactive:
	#	print
	#	print "SYSTEM",i
	#	print temp_list_inactive[i].debug()
 
	#errin = open("/data/bw/helo/error.log","a")
	#logout = open("/data/bw/helo/debug/log"+path+"_"+str(os.getpid()),"a")
	errin = open("./error.log","a")
	logout = open("./log"+source+"_"+str(os.getpid()),"w")
	start = time.time()
#	meant = 0
	cnt=0
	count_data = 0
	while True:
		data = sys.stdin.readline()
		if len(data)==0:
			break
		#print data
		if len(data)<1:
			continue
		lag_check=0
		count_data = count_data+1
		if count_data == th_lag_check:
			count_data=0
			lag_check=1
		st=time.time()
		logout.write(str(st)+" Receive message: "+data);
		ret = analyze_message(temp_list, temp_list_inactive, data, th_update, lag_check,logout)
#		meant = meant + time.time()-st

		logout.write(str(time.time())+" Processed message - total duration: "+str(time.time()-st)+"\n")
		cnt=cnt+1

		if ret<0:
			temp = download_templates('none')
			temp_list = temp[0]
			temp_list_inactive = temp[1] 

#	print "Mean time per log message", meant/cnt
#	print cnt,"messages classified"
	errin.close()
	#logout.close()
	elapsed = (time.time() - start)
	print "Total time elapsed:",elapsed
	

# call main fuction
if __name__=='__main__':
	main()

