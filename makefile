#HELO (Hierarchical Event Log Organiser) 
#version 2.1 (2010.06.13)
#The tool represent a C algorithm for log file message classification

#Created by
#Ana Gainaru

#Advisors: Franck Cappello, Stefan Trausan-Matu, Bill Kramer

# (C) 2010 by UIUC, INRIA, NCSA, UPB.
#See COPYRIGHT in top-level directory.



SHELL    = /bin/bash
CC       = gcc
CFBASE   = -Wall -g #-pedantic $(ADDFLAGS) \
#           -I$(UTILDIR) -I$(MATHDIR) -I$(TRACTDIR)
CFLAGS   = $(CFBASE) -DNDEBUG -O3
# CFLAGS   = $(CFBASE) -DNDEBUG -O3 -DBENCH
# CFLAGS   = $(CFBASE) -DNDEBUG -O3 -DARCH64
# CFLAGS   = $(CFBASE) -g
# CFLAGS   = $(CFBASE) -g -DARCH64
# CFLAGS   = $(CFBASE) -g -DSTORAGE $(ADDINC)
LDFLAGS  =
LIBS     = -lm
# ADDINC   = -I../../misc/src
# ADDOBJ   = storage.o


OBJS     = group.o
PRGS     = group 

#-----------------------------------------------------------------------
# Build Program
#-----------------------------------------------------------------------
all:       $(PRGS)

group:   $(OBJS) makefile
	$(CC) $(LDFLAGS) $(OBJS) $(LIBS) -o $@

#-----------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------

group.o: group.c makefile
	$(CC) $(CFLAGS) -c group.c -o $@


#-----------------------------------------------------------------------
# Run Program
#-----------------------------------------------------------------------

run: group
	./$(PRGS) -g60 test

#-----------------------------------------------------------------------
# Clean up
#-----------------------------------------------------------------------
localclean:
	rm -f *.o *~ *.flc core $(PRGS)

clean:
	$(MAKE) localclean
#	cd $(UTILDIR);  $(MAKE) clean
#	cd $(MATHDIR);  $(MAKE) clean
#	cd $(TRACTDIR); $(MAKE) clean

