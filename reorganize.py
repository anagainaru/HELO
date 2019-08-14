#HELO (Hierarchical Event Log Organiser) 
#version 2.1 (2010.10.27)
#The tool represents a C algorithm for log file message classification

#Created by
#Ana Gainaru

#Advisors: Franck Cappello, Stefan Trausan-Matu, Bill Kramer

# (C) 2010 by UIUC, INRIA, NCSA, UPB.
#See COPYRIGHT in top-level directory.



#!/usr/bin/env python
import sys
import string
import os

# read the template list form the given file
def read_templates(filename):
	temp_list=[]
	in_f = open(filename,"r")

	# for each line in the file,
	for temp in in_f:
		# split each template into words
		temp = temp.split("\n")[0].split(" ")
		temp = [i for i in temp if i!=""]

		# and store them into o list
		temp_list.append(temp)
	
	in_f.close()
	return temp_list


# check similarity between hybrid words
def hybrid_words(wrd1,wrd2):
	hybrid = [".", "=", ":", "-", "(", "["]

	for i in hybrid:
		idx1 = wrd1.find(i)
		if idx1==-1:
			continue
		idx2 = wrd2.find(i)
		if idx2==-1:
			continue
		if wrd1[:idx1]==wrd2[:idx2]:
			return 1
	return -1


def combine(temp1, temp2):
	lentm = min(len(temp1),len(temp2))
	newtemp = []
	for i in range(lentm):
		if temp1[i]==temp2[i]:
			newtemp.append(temp1[i])
			continue
		if temp1[i]=="n+":
			newtemp.append(temp1[i])
			break
		if temp2[i]=="n+":
			newtemp.append(temp2[i])
			break
		if temp1[i]=="*":
			newtemp.append(temp1[i])
			continue
		if temp2[i]=="*":
			newtemp.append(temp2[i])
			continue
		if hybrid_words(temp1[i],temp2[i])==1:
			newtemp.append(temp1[i])
			continue
		newtemp.append("*")
#	if len(temp1)!=len(temp2):
#		newtemp.append("n+")
	return newtemp

# compare temp1 and temp2
def compare_temp(temp1, temp2):
	wrd=0
	sim=0
	#print "compare",temp1,temp2
	lentm = min(len(temp1),len(temp2))
	if lentm<=1:
		return -1
	# if the length difference between templates is bigger than a threshold, return -1
	if lentm*100/max(len(temp1),len(temp2)) < 40:
		return -1

	for i in range(lentm):
		if temp1[i]==temp2[i]:
			sim=sim+1
			continue
		if temp1[i]=="n+":
			sim=sim+1
			break
		if temp2[i]=="n+":
			sim=sim+1
			break	
		if temp1[i]=="*":
			sim=sim+1
			wrd=wrd+1
			continue
		if temp2[i]=="*":
			sim=sim+1
			wrd=wrd+1
			continue
		if hybrid_words(temp1[i],temp2[i])==1:
			sim=sim+1
			continue
		wrd=wrd+1

	if len(temp1)!=len(temp2):
		wrd=wrd+1

	simval = sim*100/lentm
	wld = wrd*100/lentm
	#print sim, wrd, lentm

	#check the number of wildcards
	if wld>=100 or (wld>40 and simval<100):
		return -1
	#check the similarity
	if simval>80:
		ret = combine(temp1, temp2)
		#print "combine",ret
		return ret
	return -1
	

# reorganize the templates
def reorganize(temp_list, outfile):
	#print len(temp_list)
	del_list=[]

	# check templates between each other
	for tempi in range(len(temp_list)):
		# keep track if another template is similar to this one
		fnd=0
		if tempi in del_list:
			continue
		for tempj in range(tempi+1,len(temp_list)):
			# compare the two templates
			ret = compare_temp(temp_list[tempi], temp_list[tempj])
			# in case of strong similarity
			if ret!=-1:
				# change the template with the new one
				temp_list[tempi]=ret
				# set for deleting the second template from the list
				if tempj not in del_list:
					del_list.append(tempj)

	print "Merged templates:",len(del_list),"pairs"
	del_list.sort()
	del_list.reverse()
	# delete everything we set
	for i in del_list:
		del temp_list[i]

	#print len(temp_list)
	out_f = open(outfile,"w")
	for i in temp_list:
		#print i
		out_f.write(' '.join(i)+" \n")
	out_f.close()

# the main function
def main():
	out_f = "output/out.temp"

	# verifing command line arguments
	if len(sys.argv)<2:
		print "Usage:",sys.argv[0]," template_file [output_file]"
		print "If output is not provided the templates will be hold in ./output/out.templ"
		return

	if len(sys.argv)>2:
		out_f = sys.argv[2]

	# read the template list from the file
	filename = sys.argv[1]
	temp = read_templates(filename)
	#print temp
	# reorganize the templates
	reorganize(temp, out_f)

	print "Output stored in",out_f
	
	os.system("rm "+filename)

# call main fuction
if __name__=='__main__':
   main()
