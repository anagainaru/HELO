#!/usr/bin/env python
#coding=utf-8
import sys
import stopwords


# split the event set according to the separation words
def split_events(events, words, parent):
    c={}
    for evnt in events:
	#print "event: ",evnt
	countmax = 0
	wrdmax = "other "+parent
	for wrd in words:
	    # count the number of times the word is in the event description
	    countwrd = evnt.count(wrd)
	    if countmax < countwrd:
		countmax = countwrd
		wrdmax = wrd+" "+parent
	if wrdmax in c:
	    c[wrdmax].append(evnt)
	else:
	    c[wrdmax]=[]
	    c[wrdmax].append(evnt)
    return c		


def keyword_len(parents):
    nowrd = 0
    for wrd in parents:	
	if wrd=="other":
	    continue
	else:
	    nowrd += 1
    return nowrd

# find the most frequent words
def find_split_words(templates, parents):
    splitwrd = {}
    nokeys = keyword_len(parents.split(" "))
    totalwrd = 0
    notmp = 0
    for tmp in templates:
	line = tmp.split(" ")
	# investigate each word in the line
	for wrd in line:
	    totalwrd += 1
	    if len(wrd)<=1:
		continue
	    if wrd[len(wrd)-1]=="\n":
		wrd = wrd[0:len(wrd)-1]
	    #eliminate wildcards
	    if check_wilecard(wrd)==True:
		continue
	    # count how many times the word appears
	    if wrd in splitwrd:
                splitwrd[wrd]=splitwrd[wrd]+1
            else:
                splitwrd[wrd]=1
	notmp += 1
    meanwrd = (float)(totalwrd)/ notmp
    #print totalwrd, notmp, (float)(totalwrd)/ notmp, "<- mean ; procentaj ->", nokeys, nokeys/meanwrd
    if (nokeys/meanwrd)>0.2:
	return -1
    maxwrd = 0
    maxdesc = []
    # get the most frequent words
    for wrd in splitwrd:
	if wrd in parents:
	    continue
	if maxwrd == splitwrd[wrd]:
	    maxdesc.append(wrd)
	if maxwrd < splitwrd[wrd]:
	    maxwrd = splitwrd[wrd]
	    maxdesc = [wrd]
    #print maxwrd
    #print maxdesc
    return maxdesc


def write_group(name,groups):
    print "Keywords: ",
    nlist = name.split(" ")
    nlist = nlist[0:len(nlist)-1]
    for nm in nlist:
	if nm != "other":
	    print nm,
    print ""
    for grp in groups:
	print grp
    print "-----------------"

def create_groups(tgroup, i):
    for grp in tgroup:
	if len(tgroup[grp])<=2:
		write_group(grp,tgroup[grp])
		continue
	nokeys = keyword_len(grp.split(" "))
	#if nokeys>=3:
	#	print "keys>3"
	#	write_group(grp,tgroup[grp])
	#	continue
	# find new values for maxdesc
	maxdesc = find_split_words(tgroup[grp], grp)
	if maxdesc==-1:
		write_group(grp,tgroup[grp])
		continue
	# resplit the clusters
	groupaux = split_events(tgroup[grp], maxdesc, grp)

	create_groups(groupaux, i+1) 


# eliminate wildcards and stop words
def check_wilecard(wrd):
    if wrd not in stopwords.stop_words and wrd not in stopwords.wildcards:
	return False
    return True

# get the initial frequent words and events
def get_data_set(filename):
    # open file
    f=open(filename,'r')
    events = []
    splitwrd = {}
    totalwrd = 0

    # read all file lines
    for line in f:
	events.append(line)
	line = line.split(" ")
	# investigate each word in the line
	for wrd in line:
	    totalwrd += 1
	    if len(wrd)<=1:
		continue
	    if wrd[len(wrd)-1]=="\n":
		wrd = wrd[0:len(wrd)-1]
	    #eliminate wildcards
	    if check_wilecard(wrd)==True:
		continue
	    # count how many times the word appears
	    if wrd in splitwrd:
                splitwrd[wrd]=splitwrd[wrd]+1
            else:
                splitwrd[wrd]=1
    f.close()
    maxwrd = 0
    maxdesc = []
    # get the most frequent words
    for wrd in splitwrd:
	if maxwrd == splitwrd[wrd]:
	    maxdesc.append(wrd)
	if maxwrd < splitwrd[wrd]:
	    maxwrd = splitwrd[wrd]
	    maxdesc = [wrd]
	#if splitwrd[wrd] > 4:
	#    print wrd,splitwrd[wrd],totalwrd, float(splitwrd[wrd])*100/totalwrd
    #print maxwrd
    #print maxdesc

    tgroup = split_events(events, maxdesc, "")
    create_groups(tgroup, 2)


# the main function
def main():
    events = get_data_set(sys.argv[1])

# call main fuction
if __name__=='__main__':
    main()
