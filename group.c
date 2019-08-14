/*
HELO (Hierarchical Event Log Organiser) 
version 2.1 (2010.10.27)
The tool represents a C algorithm for log file message classification

Created by
Ana Gainaru

Advisors: Franck Cappello, Stefan Trausan-Matu, Bill Kramer

 (C) 2010 by UIUC, INRIA, NCSA, UPB.
See COPYRIGHT in top-level directory.

*/

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <assert.h>

#define PRGNAME     "HELO"
#define DESCRIPTION "HELO (Hierarchical Event Log Organiser)"
#define AUTHOR "Created by Ana Gainaru"
#define LICENCE "CopyRight (c) 2010-2012, UIUC, INRIA, UPB" 
#define VERSION     "version 1.7 (2010.06.13)"


/* error codes */
#define E_NOMEM	     (-1)	/* not enough memory */
#define E_FOPEN	     (-2)	/* cannot open file */
#define E_FREAD	     (-3)	/* read error on file */
#define E_OPTION     (-5)       /* unknown option */
#define E_OPTARG     (-6)       /* missing option argument */
#define E_ARGCNT     (-7)       /* too few/many arguments */
#define E_STDIN      (-8)       /* double assignment of stdin */
#define E_TARGET     (-9)       /* invalid target type */
#define E_SIZE      (-10)       /* invalid set/rule size */
#define E_SUPP      (-11)       /* invalid support */
#define E_CONF      (-12)       /* invalid confidence */
#define E_MEASURE   (-13)       /* invalid evaluation measure */
#define E_NOTRANS   (-14)       /* no items or transactions */
#define E_NOFREQ    (-15)       /* no frequent items */
#define E_UNKNOWN   (-24)       /* unknown error */

#define MSG         fprintf     /* print messages */

/*----------------------------------------------------------------------
  Constants
----------------------------------------------------------------------*/
static const char *errmsgs[] = {
  /* E_NONE      0 */  "no error\n",
  /* E_NOMEM    -1 */  "not enough memory\n",
  /* E_FOPEN    -2 */  "cannot open file %s\n",
  /* E_FREAD    -3 */  "read error on file %s\n",
  /* E_FWRITE   -4 */  "write error on file %s\n",
  /* E_OPTION   -5 */  "unknown option -%c\n",
  /* E_OPTARG   -6 */  "missing option argument\n",
  /* E_ARGCNT   -7 */  "wrong number of arguments\n",
  /* E_STDIN    -8 */  "double assignment of standard input\n",
  /* E_TARGET   -9 */  "invalid target type '%c'\n",
  /* E_SIZE    -10 */  "invalid threshold size %d\n",
  /* E_SUPP    -11 */  "invalid minimum support %g%%\n",
  /* E_CONF    -12 */  "invalid minimum confidence %g%%\n",
  /* E_MEASURE -13 */  "invalid evaluation measure "
                         "or aggregation mode %c\n",
  /* E_NOTRANS -14 */  "no items or transactions to work on\n",
  /* E_NOFREQ  -15 */  "no frequent items found\n",
  /* E_ITEMEXP -16 */  "file %s, record %d: item expected\n",
  /* E_ITEMWGT -17 */  NULL,
  /* E_DUPITEM -18 */  "file %s, record %d: duplicate item %s\n",
  /* E_FLDCNT  -18 */  "file %s, record %d: too many fields\n",
  /* E_APPEXP  -19 */  "file %s, record %d: "
                         "appearance indicator expected\n",
  /* E_UNKAPP  -21 */  "file %s, record %d: "
                         "unknown appearance indicator %s\n",
  /* E_PENEXP  -22 */  NULL,
  /* E_PENALTY -23 */  NULL,
  /* E_UNKNOWN -24 */  "unknown error\n"
};


/*----------------------------------------------------------------------
  Global Variables
----------------------------------------------------------------------*/
static int  MAX_WSIZE = 7000;
static int  MAX_WCOUNT = 50;
static char DELIM[1] = " ";
static char TOKDELIM[1] = " ";
static char     *prgname;
static FILE     *in     = NULL; /* input  file */
static FILE     *out    = NULL; /* output file */
static int  th_good  = 40;         /* threshold for cluster goodness */   
char *fn_in   = NULL;      /* name of input  file */
int start_msg = 0; /* the position where the message starts; default 9 because in blue gene the message starts from the 9th position */

/*----------------------------------------------------------------------
  Error function
---------------------------------------------------------------------*/
static void error (int code, ...)
{                               

  va_list    args;              /* list of variable arguments */
  const char *msg;              /* error message */

  assert(prgname);              /* check the program name */
  if (code < E_UNKNOWN) code = E_UNKNOWN;
  if (code < 0) {               /* if to report an error, */
    msg = errmsgs[-code];       /* get the error message */
    if (!msg) msg = errmsgs[-E_UNKNOWN];
    fprintf(stderr, "\nERR %s: ", prgname);
    va_start(args, code);       /* get variable arguments */
    vfprintf(stderr, msg, args);/* print error message */
    va_end(args);               /* end argument evaluation */
  }
  exit(code);                   /* abort the program */
}  


/*----------------------------------------------------------------------
  String manipulation function
----------------------------------------------------------------------*/

/* converts a string to lower caracters */
static void uptolow(char *str)
{
	char *p;
	for (p = str; *p != '\0'; p++)
	{
		*p = (char)tolower(*p);
	}
}


/*----------------------------------------------------------------------
  Cluster functions
----------------------------------------------------------------------*/
/* 
Description: Add a message string to one of the clusters
Input parameters: 
	- s : the string message
	- level : the iteration number in the algorithm
	- cl : clustere id 
*/
static void add_message_to_cluster(char *s, int level, int cl)
{
	char buffer[100];	
	sprintf(buffer,"output/%s_l%dc%d", fn_in, level,cl);
	//printf("Add %s in cluster %s\n",s,buffer);

	out = fopen(buffer, "a");
	/* check for errors at open */
	if(out==NULL) {
	    //error(E_FOPEN, buffer);
	    return;
	}

	fprintf(out,"%s\n",s); 

	if(out==NULL) {
	    //error(E_FOPEN, buffer);
	    return;
	}

	if(fclose(out)!=0)
		printf("Eroare la inchiderea fisierului");

}

/* 
Description: checks the relevant parts from a hybrid word and clusters the token accordingly
Input parameters:
	- buffer : the filename that contains the clusters
	- s : the message
	- str1 : the word to be investigated
	- str2 : the second word
	- level : the iteration number in the algorithm
	- cl_current : the current clusteres for this level 
	- i : the cluster number for this loop  
Output:
	- 1 in case we classify the word and 0 otherwise
 */
static int checksemantics(char *s, char* str1, char *str2, int level, int cl_current, int i)
{
	char buffer[150];
	char hybrid[6][2] = { ".", "=", ":", "-", "(", "[" }; 
	int j;

	for(j=0;j<6;j++)
	{
		/* if the words are not the same we check if str1 has one of the hybrid characters in the words */
		char *pch = strstr(str1,hybrid[j]);
		if(pch)
		{
			if(pch-str1>0)
			{
				char * aux = (char*) calloc ((pch-str1+1),sizeof(char));
				strncpy(aux, str1, pch-str1);
				sprintf(buffer,"%s%s", aux, hybrid[j]);
				if(aux) free(aux); //aux=NULL;

				/* if we can find a token in the word list equal to aux then return */
				if(strstr(str2, buffer) != NULL)
				{
					/* the message will be part of the cluster with id i */
					add_message_to_cluster(s,level+1,cl_current+i);

					return 1;	
				}
			}
		}
	}


	/* if the message has a numeric value we use the cluster that has numar in the list */
	if(isdigit(str1[0])!=0 && strstr(str2, "numar")!=NULL)
	{
		/* the message will be part of the cluster with id i */
		add_message_to_cluster(s,level+1,cl_current+i);
			
		return 1;	
	}
	
	return 0;
}

/* 
Description: Devide a cluster acording to a specific position in the message description
Input parameters:
	- buf : the filename that contains the cluster
	- tok : splitting position
	- words : the unique tokens from tok position
	- nr_words : the number of unique tokens
	- level : the iteration number in the algorithm
	- cl : clustere id that needs to be split 
Output:
	- next cluster id
 */
static int split_cluster(char *buf, int tok, char * words, int nr_words, int level, int cl_current)
{
	int i;
	char *str1, *auxwords, *str2, *auxwordstok, *s=NULL;
	size_t len = 0;
	ssize_t read;

	auxwords = (char *) malloc(500*sizeof(char));
	auxwordstok = (char *) malloc((strlen(words)+1)*sizeof(char));

	in = fopen(buf, "r");
	/* check for errors at open */
	if(in==NULL) {
	    printf("ERR canot open file %s\n", buf);
	    return cl_current;
	}

//	printf("\n");
	printf("Split Cluster In %d for position %d\n",nr_words,tok);
//	printf("Unique tokens %s for position %d\n",words,tok);
//	printf("\n");

	/* read each message form the log file */
	while ((read = getline(&s, &len, in)) != -1) {
		if(strcmp(s," ")!=0)
		{ 
			char *newline = strchr(s, '\n' );
			if ( newline )
				*newline = 0;

			//printf("Read line: %s\n",s);

			/* transform message in lower case */
			uptolow(s);

		 	/* write s in the file that describes its cluster */
			strncpy(auxwords, s, 500);

			/* we need the word in the tok position */	

			str1 = strtok(auxwords, DELIM);

			i=0;
			while (str1 != NULL)
			{
				i++;
				if(i==start_msg+1+tok) break;
				str1 = strtok(NULL, DELIM);
			}
			i = i-start_msg-1;

			if(i<tok)
			{
				//printf("Add to last cluster: %d\n",cl_current+nr_words-1);
				/* add the message in the last cluster */
				add_message_to_cluster(s,level+1,cl_current+nr_words-1);
				
				continue;
			}

			strcpy(auxwordstok, words);
			str2 = strtok(auxwordstok, TOKDELIM);

			i=0;
			/* loop through the uniq tokens */
			while (str2 != NULL)
			{
				/* if the word from the message form position tok is the one from the string of tokens from position i*/
				if(strcmp(str1, str2) == 0)
				{
					//printf("Add to last cluster: %d\n",cl_current+i);
					/* the message will be part of the cluster with id i */
					add_message_to_cluster(s,level+1,cl_current+i);

					break;
				}

				if(checksemantics(s,str1,str2,level,cl_current,i)==1) break;
				
				if(i==nr_words-1) break;
				i++;
				str2 = strtok(NULL, TOKDELIM);

			}
			
		} 
	}
	
	fclose(in);

	if(auxwordstok) free(auxwordstok);
	if(auxwords) free(auxwords);
	if(s) free(s);

	return cl_current+nr_words;
}

/*
Description: returns the output string for hybrid tokens
Input parameters:
	- str1 : the word from the group
	- del : the delimitator
	- word : the word from the description
*/
static char* out_hybrid(char *str1, char* del, char* word)
{
	char buffer[200];				
	char *aux, *pch = strstr(str1,del);

	if(pch && pch-str1>0)
	{
		aux = (char*) calloc ((pch-str1+1),sizeof(char));
		strncpy(aux, str1, pch-str1);
		sprintf(buffer,"%s%s", aux, del);
		if(aux) free(aux);

		if(strstr(word, buffer) != NULL)
		{
			char *buffer2 = (char *) malloc((strlen(buffer)+3)*sizeof(char));

			if(strcmp(del,"(")==0)
			{
				sprintf(buffer2,"%s*)", buffer);
				return buffer2;	
			}
			if(strcmp(del,"[")==0)
			{
				sprintf(buffer2,"%s*]", buffer);
				return buffer2;	
			}
			sprintf(buffer2,"%s*", buffer);
			return buffer2;			
		}
		else return "*";
	}

	return NULL;

}


/* 
Description: Format all messages from one cluster into a single line
Input parameters:
	- level : the iteration number in the algorithm
	- cl : clustere id that needs to be split 
 */
static void print_format_cluster(int level, int cl_current)
{
	int i,j;
	char buffer[100], *s = NULL;
	char **words, *str1;
	size_t len=0, read;

	words = (char**)malloc(MAX_WCOUNT*sizeof(char*));
	if (!words) { printf("ERR Not enough memory\n"); return; } 

	for(i=0;i<MAX_WCOUNT;i++)
	{
		words[i] = (char*)malloc(300*sizeof(char));
		strcpy(words[i], "");
	}

	for(j=0;j<cl_current;j++)
	{
		sprintf(buffer,"output/f%s_l%dc%d", fn_in, level,j);
	
		in = fopen(buffer, "r");
		/* check for errors at open */
		if(in==NULL) {
		    //printf("ERR cannot open file %s\n", buffer);
		    continue;
		}

		for(i=0;i<MAX_WCOUNT;i++)
			strcpy(words[i], "");

		/* for each cluster we format the messages into one line */
		while ((read = getline(&s, &len, in)) != -1) {		
			if(strcmp(s," ")!=0)
			{ 
				/* transform message in lower case */
				uptolow(s);

			 	/* parse the message and extract the word structure */
				str1 = strtok(s, DELIM);
				i=0; 
				
				/* loop until we have the start_msg-th word - that is where the message starts */
				while (1)
				{
					if(i==start_msg) break;
					i++;
					if(str1==NULL) break;
					str1 = strtok(NULL, DELIM);
				}
				
				if(i<start_msg) continue;

				for(i=0;i<MAX_WCOUNT;i++)
				{
					if(str1==NULL)
					{ 
						if(strcmp(words[i],"s+")==0) break;

						if(strcmp(words[i],"")!=0)
						{
							strcpy(words[i],"n+");
						}
						else{
							strcpy(words[i],"s+");
						}
						break;
					}
					//printf("%d - %s %s\n",i,words[i],str1);

					if(strcmp(words[i],"n+")==0) break;
					if(str1[strlen(str1)-1]=='\n') str1[strlen(str1)-1]='\0';

					/* if the final word is empty then this is the first message in the list */
					if(strcmp(words[i],"s+")==0)
					{
						strcpy(words[i],"n+");
						break;
					}

					/* if the final word is empty then this is the first message in the list */
					if(strcmp(words[i],"")==0)
					{
						/* we copy the word in the message into the final word */
						int len=strlen(str1);
						if(len>300) len=299;
						strncpy(words[i],str1,len+1);
					}else{
						int len=strlen(str1);
						if(len>300) len=300;
						/* if we already have a value for the word then see if is the same with the current word */
						if(strncmp(words[i],str1,len)!=0)
						{
							if(strcmp(words[i],"*")!=0 && isdigit(str1[0]))
								strcpy(words[i],"d+");
							else
							{
								int gasit=0; 
								char del[2]; 
								char hyb[6][2] = { ".", "=", ":", "-", "(", "[" }; 
								int j;

								for(j=0;j<6;j++)
								{
									strcpy(del,hyb[j]);

									char *out_gasit = out_hybrid(str1,del,words[i]);
									if(out_gasit!=NULL)
									{
										gasit = 1;
										strcpy(words[i],out_gasit);
										if(strcmp(out_gasit,"*")!=0){
											free(out_gasit);
										}
										break;
									} 
								}

								if(gasit==0)
								{
									/* if the two words are not the same we put * instead of any word */
									strcpy(words[i],"*");
								}
							}
							
						}
					}	
					
					str1 = strtok(NULL, DELIM);
				}
			} 
		}


		fclose(in);

		sprintf(buffer,"output/%s_aux", fn_in);
		FILE *out = fopen(buffer, "a");
		int op_f=0;
		/* check for errors at open */
		if(out==NULL) {
		    printf("ERR cannot open file %s\n", buffer);
		    op_f=1;
		}

		//printf("Cluster %d\n",j);
		/* print the sequence of words for each cluster */
		for(i=0;i<MAX_WCOUNT;i++)
		{
			if(strcmp(words[i],"")==0)
			{ 
				break;
			}
			if(strcmp(words[i],"s+")==0) break;
			if(strcmp(words[i],"n+")==0)
			{ 
				//printf("%s ",words[i]); 
				if(op_f==0) fputs(strcat(words[i],DELIM),out);
				break;
			}
			
			//printf("%s ",words[i]); 
			if(op_f==0) fputs(strcat(words[i],DELIM),out);
		}

		//printf("\n");
		fputs ("\n",out); 
	}

	for(i=0;i<MAX_WCOUNT;i++)
	{
		if(words[i]) free(words[i]);
	}

	if(words) free(words);
	if(s) free(s);
}

/*----------------------------------------------------------------------
  Read file functions
----------------------------------------------------------------------*/

/*
Description: checks if a hybrid word is a new word in the list of unique tokens
Input parameters:
	- str1 : the word that we are checking
	- del : the delimitoator word
	- word_tokens : the list of unique tokens on one position 
*/
static int unique_hibrid(char *str1, char *del, char *word_tokens)
{
	char buffer[205];

	char *pch = strstr(str1,del);
	if(pch)
	{
		if(pch-str1>0)
		{
			char *aux = (char*) calloc ((pch-str1+1),sizeof(char));
			strncpy(aux, str1, pch-str1);
			sprintf(buffer,"%s%s", aux, del);
			if(aux) free(aux); //aux=NULL;
			/* if we can find a token in the word list equal to aux then return */
			if(strstr(word_tokens, buffer) != NULL) return 1;
		}
	}

	return 0;
}


/* 
Description: Refresh the number of unique tokens for words in the specific position
Input parameters:
	- num_tokens : the number of words in word_tokens
	- word_tokens : the string that contains the unique tokens on the specific position so far 
	- str1 : the word on the specific position from the message from the log file 
Output:
	- word_tokens : will contain the refresh list of unique words 
	- the number of words in word_tokens
 */
static int unique_tokens(int num_tokens, char *word_tokens, char *str1)
{
	char buffer[205];
	char *temp = (char *) malloc(200*sizeof(char));
	int leng = strlen(str1), fnd=0;
	if(leng>200) leng=199;
	strncpy(temp,str1,leng+1);	
	
	sprintf(buffer," %s ", temp);
	if(strstr(word_tokens, buffer) != NULL)
		fnd=1;

	sprintf(buffer,"%s ", temp);
	if(fnd==0 && strncmp(buffer, word_tokens, leng+1)==0)
		fnd=1;

	if(temp) free(temp);

	/* if str1 is a new token */
	if(fnd==0)
	{
		char hyb[6][2] = { ".", "=", ":", "-", "(", "[" }; 
		int j;

		for(j=0;j<6;j++)
		{
			if(unique_hibrid(str1, hyb[j],word_tokens)==1) return num_tokens;
		}

		/* if str1 is a numerical value we put 'numar' in the list if it's not already there */
		/* or */
		/* if str1 has the form 0x then we have a hexadecimal number and we treat it as number */
		if(isdigit(str1[0])!=0 || strncmp(str1,"0x",2)==0)
		{
			if(strstr(word_tokens, "numar") == NULL)
			{
				strcat(word_tokens,"numar");
				strcat(word_tokens,TOKDELIM);
				return num_tokens+1;
			}
			return num_tokens;
		}

		/* if str1 in a new token */	
		/* if there is no more space */
		if(strlen(word_tokens)+strlen(str1)>MAX_WSIZE)
			return num_tokens;

		strcat(word_tokens,str1);
		strcat(word_tokens,TOKDELIM);

		num_tokens++;
	}

	return num_tokens;
}

/* 
Description: Extract the number and the list of unique words form the log files
Input parameters:
	- s : the message from the log file
	- word_tokens : the structure that contains the unique tokens for each word position 
	- num_tokens : the structure that contains the number of unique tokens for each position
	- total_tokens : contains the number of total tokens for each position
	- mean_token : contains the mean number of words in all messages parsed so far from the log file
Output: 
	- the new value for the mean variable
*/
static int parse_log_files(char s[], int size_s, char **word_tokens, int *num_tokens, int *total_tokens, int mean_token)
{
	int wc = 0;
        char *str1,*aux;
	
	aux = (char *) malloc(size_s*sizeof(char));
	strcpy(aux,s);
	
        /* extract first string from the message */
        str1 = strtok(aux, DELIM);
	//printf("%d - %s\n",strlen(str1),str1);
	
        /* loop until we have all the words */
        while (1)
        {
                /* check if there is nothing else to extract */
                if (str1 == NULL)
                {
			wc=wc-start_msg;
			if(aux) free(aux); 
                        return mean_token+wc;
                }

		/* the first start_msg fields represent other informations */
		if(wc>=start_msg && wc<(MAX_WCOUNT+start_msg))
		{		
			/* if we have more then size_s words it is likely to exceed the MAX_WSIZE buffer limit for the words */
			if(num_tokens[wc-start_msg]<size_s)
				num_tokens[wc-start_msg] = unique_tokens(num_tokens[wc-start_msg], word_tokens[wc-start_msg], str1); 
			total_tokens[wc-start_msg]++;
		}

		str1 = strtok(NULL, DELIM);
                wc++;
        }
}

/* 
Description: Find the best splitting position 
Input parameters:
	- word_tokens : the structure that contains the unique tokens for each word position 
	- num_tokens : the structure that contains the number of unique tokens for each position
	- total_tokens : contains the number of total tokens for each position
	- mean : contains the mean number of words in all messages parsed so far from the log file
Output: 
	- the splitting position or -1 if the cluster doesn't need to be devided
*/
static int find_mintok(char **word_tokens, int *num_tokens, int *total_tokens, int mean)
{
	/* parse each possition of words in the message */
	int uniq = 0, mintok = 0, j;

	if(mean>MAX_WCOUNT) mean=MAX_WCOUNT;

	if(num_tokens[0]==0) return -1;

	for(j=0;j<MAX_WCOUNT;j++)
	{
		//printf("MINTOK position %d numtok %d (%d) wordtok %s\n",j,num_tokens[j],total_tokens[j],word_tokens[j]);

		/* if we have tokens for this position */
		if(num_tokens[j]>0)
		{
			/* if we have some messages with no words in this position */
			if(total_tokens[j]<total_tokens[0]) num_tokens[j]++;

			/* if the token is unique for this position we increase the uniq variable */
			if(num_tokens[j]==1)
				uniq ++;

			/* if we have more than one token in a position */
			if(num_tokens[j]>1)
			{
				if(mintok==0 && num_tokens[mintok]==1)
				{
					mintok = j;
				}
				/* compute the ratio of the number of different tokens to the total number of tokens that have a value */
				float ratio = total_tokens[j]*100/(float)total_tokens[0];
				float minaux = num_tokens[mintok]*100/ratio;
				float aux = num_tokens[j]*100/ratio;

				/* we consider the biggest value for the ratio that also has enough tokens != null */
				if(minaux > aux && total_tokens[j]>(num_tokens[j]-1)*(total_tokens[0]/num_tokens[j]))
				{
					mintok = j;
				}
				//printf("%d MINTOK (%d) minaux %f aux %f; second %f\n",j, num_tokens[j],minaux+mintok, aux+j, ratio);

			}
			
		}
	}

	if(mean<=0) return -1;

	/* the cluster goodness represents the ratio between the number of token positions that have only one unique value */
	/* to the maximum token lenght of the lines in the partiotion (or the mean if we use ntok/number of messages) */
	//printf("\nCluster goodness:%d, th_good=%d \n",uniq*100/mean,th_good);
	//printf("The best partition is for tokens in position: %d with value: %f\n", mintok, num_tokens[mintok]/(float)total_tokens[mintok]);

	/* if the cluster is not good then we start splitting */
	if(uniq*100/mean < th_good && num_tokens[mintok]>1)
	{
		return mintok;
	}
	
	return -1;
}


/* 
Description: Reads the log entries from all file clusters at the given level. The files that contain the clusters for this iteration level are named {fn_in}_l{level}c{i} with i=0..nr_cl-1
Input parameters:
	- th_good : the goodness threshold
	- level : the iteration number in the algorithm
	- nr_cl : clustere id  
*/
static void read_logs(int th_good, int level, int nr_cl)
{
	int i,j,mintok,cl_current=0;
	char buffer[50], **word_tokens, *s=NULL;
	int *num_tokens, *total_tokens, mean_token=1;
	size_t len = 0;
        ssize_t read;

	int gasit=0;

	/* initialize arrays */
	word_tokens = (char **)malloc(MAX_WCOUNT *sizeof(char *));
	if (!word_tokens) { error(E_NOMEM); return; }

	num_tokens = (int *)malloc(MAX_WCOUNT *sizeof(int));
	if (!num_tokens) { error(E_NOMEM); return; }

	total_tokens = (int *)malloc(MAX_WCOUNT *sizeof(int));
	if (!total_tokens) { error(E_NOMEM); return; }

	for(j=0;j<MAX_WCOUNT;j++)
	{
		word_tokens[j] = (char*)malloc(MAX_WSIZE*sizeof(char));
		//printf("%d Malloc %d\n",j,word_tokens[j]);
	}

	/* For each cluster, read all messages from the file and populate the word arrays */
	for(i=0;i<nr_cl;i++)
	{
		mean_token=1;
		sprintf(buffer,"output/%s_l%dc%d", fn_in, level,i);
	
		in = fopen(buffer, "r");
		/* check for errors at open */
		if(in==NULL) {	/* if the file doesn't exist, rename the final file from one level to the next */

			char buf_aux[50], buf_old[50];
			sprintf(buf_old,"output/f%s_l%dc%d", fn_in, level,i);
			sprintf(buf_aux,"output/f%s_l%dc%d", fn_in, level+1,cl_current);
			//printf("rename %s to %s \n",buf_old,buf_aux);
			rename( buf_old , buf_aux );
			cl_current++;
			continue;		    
		}

		//printf("Reading cluster %d from %d file %s ... \n", i, nr_cl, buffer);

		for(j=0;j<MAX_WCOUNT;j++)
		{
			memset(word_tokens[j],0,MAX_WSIZE);
			strcpy(word_tokens[j]," ");
			num_tokens[j] = 0;
			total_tokens[j] = 0;
		}

		j=0;
		/* read each message line form the log file */
		while ((read = getline(&s, &len, in)) != -1) {
			if(strcmp(s," ")!=0)
			{ 
				char *newline = strchr(s, '\n' );
				if ( newline )
					*newline = 0;

				//printf("%d - Read line: %s\n",level,s);
				j++;
				/* transform message in lower case */
				uptolow(s);

			 	/* parse de message and extract the word structure */
				mean_token = parse_log_files(s, len, word_tokens, num_tokens, total_tokens,mean_token);

			} 
		}
		fclose(in);

		/* then find the position in the messages with the minimal number of tokens */
		mintok = find_mintok(word_tokens, num_tokens, total_tokens, mean_token/j);

		/* if the function returns -1 then the cluster's goodness is above the treshold */
		if(mintok==-1)
		{
			char buf_aux[50];
			sprintf(buf_aux,"output/f%s_l%dc%d", fn_in, level+1,cl_current);
			//printf("rename %s \n",buf_aux);
			rename( buffer , buf_aux );
			cl_current++;
			continue;
		}

		gasit=1;

		/* if the cluster goodness is not above the treshold we divide the file into length(word_tokens[mintok]) clusters */
		cl_current = split_cluster(buffer, mintok, word_tokens[mintok], num_tokens[mintok],level,cl_current);
		//printf("Current: %d\n",cl_current);
		if(cl_current==-1) return;
	}


	/* delete all cluster files from the previous step exept the first input file */
	if(level>0)
	{
		for(i=0;i<nr_cl;i++)
		{
			sprintf(buffer,"output/%s_l%dc%d", fn_in, level,i);
			//printf("remove %s\n",buffer);
			remove(buffer);
		}
	}

     	for(j=0;j<MAX_WCOUNT;j++)
        {
		//printf("%d before free %d - %d\n",j,word_tokens[j],num_tokens[j]);
                free(word_tokens[j]);
		//printf("%d next before free %d \n",j,word_tokens[j]);
        }
	free(word_tokens);
	free(s);
	free(num_tokens);
	free(total_tokens);

	/* if all clusters have the desired goodness */
	if(gasit==0 || level>MAX_WCOUNT)
	{
		print_format_cluster(level+1, cl_current);

		/* delete the auxiliary files */ 
		if(level>0)
		{
			for(i=0;i<nr_cl;i++)
			{
				sprintf(buffer,"output/f%s_l%dc%d", fn_in, level+1,i);
				remove(buffer);
			}
		}
		return;
	}

	//printf("Restart with %d clusters\n",cl_current);
	//return;
	
	/* else restart the process with the clusters as input */
	//printf("Restart ... \n");
	if(level>15) return;
	read_logs(th_good, level+1, cl_current);

}

/*
int test(){
	char buffer[50];
	char s[500];

	sprintf(buffer,"output/%s_l0c0", fn_in);
	in = fopen(buffer, "r");
	MSG(stderr, "reading %s ... \n", buffer);

	while(!feof(in))
	{ 
	 	if(fgets(s, 500, in)==NULL)
		{
	  		break;
		}

		//printf("-%s-\n",s);

		if(strcmp(s," ")!=0)
		{
			printf("-%s-\n",s);
		}
	} 
}
*/

/*----------------------------------------------------------------------
  Main function
----------------------------------------------------------------------*/
int main(int argc, char *argv[])
{
	int  i, k = 0;          
  	char **optarg = NULL;      /* option argument */
  	char *s;
	int level=0,clusters=1,format=0;
  	             

	if (argc > 1) {
                /* if no arguments are given print a startup message */
		fprintf(stderr, "%s - %s\n", argv[0], DESCRIPTION);
		fprintf(stderr, "%s \n", VERSION);printf("%s\n", AUTHOR);
		printf("%s\n", LICENCE); } 
	else {                
		/* if arguments are not given then print a usage message and abort */      
		printf("%s\n", DESCRIPTION);
		printf("%s\n", VERSION);
		printf("%s\n", AUTHOR);
		printf("%s\n", LICENCE);
		printf("\nUsage: %s [options] name_file\nOptions:\n -g cluster goodness threshold between 0 and 100\n -m the position in the logs where the actual message starts \n-f/l level nr_clusters format clusters from files output/name_l{level}c{0..number_clusters-1} f - format; l- set level\n", argv[0]);
		return 0;     
	}

	prgname = argv[0];

	/* read the arguments */
	for (i = 1; i < argc; i++) {  
	    s = argv[i];                
	    if (optarg) { *optarg = s; optarg = NULL; continue; }
	    if ((*s == '-') && *++s) {  /* if argument is an option */
	      while (*s) {              
		/* evaluate the options */
		switch (*s++) {        
		  case 'g': th_good = (int)strtol(s, &s, 0); break;
		 // case 'd':
		  case 'm': start_msg = (int)strtol(s, &s, 0); break;
		  case 'l': level=atoi(argv[i+1]); clusters=atoi(argv[i+2]); i+=2; break;
		  case 'f': format=1; level=atoi(argv[i+1]); clusters=atoi(argv[i+2]); i+=2; break;
		  default : error(E_OPTION, *--s);          break;
		}                       
		if (optarg && *s) { *optarg = s; optarg = NULL; break; }
	      } }                       
	    else {                      
	      switch (k++) {            
		/* evaluate non-options */
		case  0: fn_in  = s;      break;
		default: error(E_ARGCNT); break;
	      }                         
	    }
	  }       

	/* check argument correctness */
	if (optarg) error(E_OPTARG);
	/* check the number of arguments */  
	if ((k < 1) || (k > 2))       
	    error(E_ARGCNT);            
	/* check the limits */
	if (th_good < 0) error(E_SIZE, th_good); 
	if (th_good > 100) error(E_SIZE, th_good);                           
        
	/* read the log files and start the splitting process */
	if(format==0) read_logs(th_good, level, clusters);
	else{
		/* or create the clusters from files */
		print_format_cluster(level, clusters);	
		if(level>0)
		{
			char buffer[50];
			for(i=0;i<clusters;i++)
			{
				sprintf(buffer,"output/f%s_l%dc%d", fn_in, level+1,i);
				remove(buffer);
			}
		}
	}

//	char cmd[100];
//	sprintf(cmd,"python reorganize.py output/%s_aux output/%s_final",fn_in, fn_in);
//	i = system(cmd);

        return 0;
}


