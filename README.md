# HELO (Hierarchical Event Log Organiser) 

*version 2.1 (2010.06.13)*

## Description

This tool classifies log messages considering their description. A log message contains constands and variables ("Accepted publickey for ip 123.456.123.456" contains 4 constants "Accepted", "publickey", "for", "ip" and one variable "123.456.123.456"). HELO is used to cluster messages that have the same constant words. 
It uses a 2 step hierarchical clustering process: 
	- in the first step the tool searchs for the best split position for each cluster (the position where there are minimum number of unique words for all log messages)
	- in the second step the clusters are divided depending on their word in the splitting position  
The process stops when all clusters have messages similar enough (the ratio of constants to all words is above a threshold). 
At the end, for each cluster, HELO creates a template by replacing variables with wildcards.

The templates given by the tool have the following format: “Accepted publickey for * from * port d+ ssh2 n+” where: 
	- * means a random token 
	- d+ a numeric token 
	- n+ one or more different tokens

Example for the input log:
Added 8 subnets and 409600 addresses to DB
address parity check..0
address parity check..1
Added 10 subnets and 589500 addresses to DB
data TLB error interrupt

Iteration 1:
- there is one cluster that contains all messages
	- Step 1 - finding the splitting position
		- Position 1 has 3 unique english words ("Added", "address", "data")
		- Position 2 has 2 unique words and numerical values (wich represents one token)
		- Position 3 has 2 unique words and one unique hybrid word ("check..")
		- Position >3 has only two log lines with words (which is not enough for the splitting process)

		- Position 1,2,3 can all be chosen for the splitting position, the resutls will be the same (lets assume 2 will be chosen by HELO)	

	- Step 2 - split the cluster into 3 sub-clusters
		- Cluster 1 will have a numerical value on position 2:
			Added 8 subnets and 409600 addresses to DB
			Added 10 subnets and 409600 addresses to DB
		- Cluster 2 will have word "parity" on position 2:
			address parity check..0
			address parity check..1
		- Cluster 3 will have word "TLB" on position 2:
			data TLB error interrupt

Iteration 2:
- for each of the 3 clusters:
	- Compute cluster goodness
		- Cluster 1: 6 constant words, 2 numerical values: goodness 92%
		- Cluster 2: 2 constant words, 1 hybrid (with the same root "check.."): goodness 100%
		- Cluster 3: goodness 100%

Create templates:
Cluster 1:
	Added 8 subnets and 409600 addresses to DB
	Added 10 subnets and 409600 addresses to DB
	template:
	Added d+ subnets and 409600 addresses to DB

Cluster 2:
	address parity check..0
	address parity check..1
	template:
	address parity check.*

Cluster 3:
	data TLB error interrupt

Creates a file in output/name_aux with the following templates:
added d+ subnets and 409600 addresses to db
address parity check.*
data tlb error interrupt

## Input file

HELO workes on log message descriptions so it assumes words can be separated from each other by a unique delimiter. The default is " ", however, this can be changed from group.c (line 89):
static char DELIM[1] = " ";
to any other character. 

The entire entry file must have the same delimiter. Example of valid log entries:
	- Separated by " "
	1117838570 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.50.363779 R02-M1-N0-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected
	- Separated by "," 
	38594712,Software_Error,CIOS,WARN,2015-04-03-06.25.36.732273,The,sysiod,process,seems,to,be,stuck,in,a,system,call,while,running.

Example of an invalid entries:
38594712,Software_Error,CIOS,WARN,2015-04-03-06.25.36.732273,The sysiod process seems to be stuck in a system call while running.
For this entrie to become valid, one can either transform all "," to " " (vim %s/,/ /g) or extract the log description from the entry (cut -d"," -f6)

## Usage

To compile the sources type in command line :
```
	make
```
To run the clustering tool:
```
	./group [options] file_name
	The input file used by the program is named {file_name}_l0c0 and is located in the output folder.
```
Options:
```
	 -g{cluster_goodness} 
	Gives cluster goodness threshold between 0 and 100 (default value 40)

	 -m{position}
	Indicates the position in the logs where the message description starts (0 means the first position in the message and so on). The separator considered is space. (default value is 0; the message only contains the description)

	 -l {level} {nr_clusters}
	Continues the clustering process after already splitted the logfile into nr_clusters groups. The files that contain the groups are named {file_name}_l{level}c{i} with i=0..nr_clusters-1 from the output folder.

	 -f {level} {nr_clusters}
	Creates the description for all clusters found in the following files output/{file_name}_l{level}c{i} with i=0..nr_clusters-1
```
Execution example:
```	
	make run
        ./group -g50 -m4 test 
	./group -m0 -l 2 10 test

```
To delete the executable and all unnecessary files type:
```
	make clean
```

## Reference paper

Ana Gainaru, Franck Cappello, Stefan Trausan-Matu, Bill Kramer - "Event log mining tool for large scale HPC systems", Euro-Par'11 Proceedings of the 17th international conference on Parallel processing - Volume Part I, Pages 52-64, 2011

```
@inproceedings{DBLP:conf/europar/GainaruCTK11,
  author    = {Ana Gainaru and
               Franck Cappello and
               Stefan Trausan-Matu and
               Bill Kramer},
  title     = {Event Log Mining Tool for Large Scale HPC Systems},
  booktitle = {Euro-Par (1)},
  year      = {2011},
  pages     = {52-64},
  ee        = {http://dx.doi.org/10.1007/978-3-642-23400-2_6},
  crossref  = {DBLP:conf/europar/2011-1},
  bibsource = {DBLP, http://dblp.uni-trier.de}
}
```
