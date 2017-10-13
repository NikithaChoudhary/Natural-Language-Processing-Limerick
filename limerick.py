#!/usr/bin/env python
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit

# Use word_tokenize to split raw text into words
from string import punctuation

import nltk
from nltk.tokenize import word_tokenize
from curses.ascii import isdigit 


scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)



class LimerickDetector:

    def __init__(self):
        """
        Initializes the object to have a pronunciation dictionary available
        """
        self._pronunciations = nltk.corpus.cmudict.dict()

#Number of Syllables
    def num_syllables(self, word):
        """
        Returns the number of syllables in a word.  If there's more than one
        pronunciation, take the shorter one.  If there is no entry in the
        dictionary, return 1.
        """
      
        c=0 #initial count
        tc = [] #total count
        
        #Check if the punctuation is a word
        if word in ('.', ',', '!', '?', ':', ';', '`', '-', '()', '[]', '(', ')', '[', ']', '\'', '\"\"', '\'\'', '\"','``',''): 
           return 0
        
        #if not a punctuation
        if word.lower() in self._pronunciations:
           for x in self._pronunciations[word.lower()]:
              for y in x:
                 if y[-1].isdigit(): 
                    c=c+1 #if digit at the end ie., syllables, increase count
              tc.append(c) #append the count, if the word has 2 pronounciations
              c = 0 #reset the count to 0
              return min(tc) #Find the minimum of the total count ie., take the shorter one
       
        #count= max([len([y for y in x if isdigit(y[-1])]) for x in pronunciations[word.lower()]])
        #return count
        else:
            return 1

#Rhyme or not
    def rhymes(self,a, b):
        str1=[]
        str2=[]
        res=[]
        res2=[]
    
    #1st word 
        if a.lower() in self._pronunciations:
            for x in self._pronunciations[a.lower()]:
            #print(x)
                str1.append(x)
        #print("w1", str1)
    
            for x in str1:
                first= x[0][0] 
                if first in ('aeiouAEIOU'): #If it starts with vowel, return the entire word
                #print ("first letter is vowel", first)
                    res.append(x[:])    
                    break
                else:  #Else consonant
                    for each in x:
                    #print each
                        if each[0] in ('aeiouAEIOU'): #iterate until the vowel is found in the word 
                        #print "vowel"
                            ind = x.index(each)
                            res.append(x[ind:])
                        #print res
                            break #if the word has no vowels
                        else:
                            if x.index(each) == len(x)-1:
                                res.append([])
                            continue
        else:
            return False
	#2nd word
        if b.lower() in self._pronunciations:
            for x in self._pronunciations[b.lower()]:
            #print(x)
                str2.append(x)
        #print("w2", str2)
    
            for x in str2:
                first= x[0][0] 
                if first in ('aeiouAEIOU'): #If it starts with vowel, return the entire word
                #print ("first letter is vowel", first)
                    res2.append(x[:])    
                    break
                else:
                    for each in x:
                    #print each
                        if each[0] in ('aeiouAEIOU'):  #iterate until the vowel is found in the word 
                        #print "vowel"
                            ind = x.index(each)
                            res2.append(x[ind:])
                        #print res2
                            break
                        else: #if the word has no vowels
                            if x.index(each) == len(x)-1:
                                res2.append([])
                            continue
        else:
            return False
     
        cartProduct = [(x,y) for x in res for y in res2] #Cartitian Prod of the result to check for matching tupples
    #print(cartProduct)
    
        for (first, second) in cartProduct: 
        #print(first,second)
            if not first: 
                return True
            if not second:
                return True
            if(len(first) == len(second)):
                if first == second:
                    return True
            if(len(first) > len(second)):
                if first[len(first) - len(second):] == second[:]:
                    return True
            if(len(first) < len(second)):
                if second[len(second) - len(first):] == first[:]:
                    return True
        return False
 
#Check for Limerick
    def is_limerick(self,text):
        """
        Takes text where lines are separated by newline characters.  Returns
        True if the text is a limerick, False otherwise.

        A limerick is defined as a poem with the form AABBA, where the A lines
        rhyme with each other, the B lines rhyme with each other, and the A lines do not
        rhyme with the B lines.


        Additionally, the following syllable constraints should be observed:
          * No two A lines should differ in their number of syllables by more than two.
          * The B lines should differ in their number of syllables by no more than two.
          * Each of the B lines should have fewer syllables than each of the A lines.
          * No line should have fewer than 4 syllables

        (English professors may disagree with this definition, but that's what
        we're using here.)


        """
        #print (text)
        rm_spc = text.strip()
        #print (rm_spc)
        output = rm_spc.split('\n')
        #print (output)
        rhymeWords = []
        if len(output) != 5:
            #print("not 5 lines")
            return False
        
        else:
            #print ("Satisfies 5 line constarint")
            count = 0
            tc = []
            sentence_tokenize = [word_tokenize(i) for i in output]
            #print ("yeah", sentence_tokenize)
            for i in range(len(sentence_tokenize)): #If the word is only a special char, remove it from the tokenized array
                if sentence_tokenize[i][-1] in ('.', ',', '!', '?', ':', ';', '`', '-', '()', '[]', '(', ')', '[', ']', '\'', '\"\"', '\'\'', '\"','``',''):
                    sentence_tokenize[i] = sentence_tokenize[i][:-1]
                
            #print ("yeah", sentence_tokenize)
            for i in range(len(sentence_tokenize)):
                for j in range(len(sentence_tokenize[i])):
                    if j == len(sentence_tokenize[i]) - 1:
                        rhymeWords.append(sentence_tokenize[i][j])
                    count = count + self.num_syllables(sentence_tokenize[i][j])
                tc.append(count)
                count = 0
                
            #print(tc)
            # Syllable difference if greater than 2, Not Limerick !
            if tc[0] - tc[1] >2 : #Check 
                #print("a")
                return False
            if tc[0] - tc[4] >2 :
                #print("b")
                return False
            if tc[1] - tc[4] >2 :
                #print("c")
                return False
            if tc[2] - tc[3] >2 :
                #print("d")
                return False
              
            #B should have fewer syllables than A
            if tc[0] - tc[2] <=0 :
                #print("e")
                return False
            if tc[0] - tc[3] <=0 :
                #print("f")
                return False
            if tc[1] - tc[2] <=0 :
                #print("g")
                return False
            if tc[1] - tc[3] <=0 :
                #print("h")
                return False
            if tc[4] - tc[2] <=0 :
                #print("i")
                return False
            if tc[4] - tc[3] <=0 :
                #print("j")
                return False
            
            # Check if all sentences in A and B have min 4 syllables
            for i in range(len(tc)):
                if tc[i] < 4:
                    #print("k")
                    return False
             
             
            #Check if the A = 1,2 and 5 end words rhyme and B = 3,4 rhyme
            if (self.rhymes(rhymeWords[0],rhymeWords[1])) == False :
                #print("1")
                return False
            if (self.rhymes(rhymeWords[0],rhymeWords[4])) == False :
                #print("2")
                return False
            if (self.rhymes(rhymeWords[1],rhymeWords[4])) == False :
                #print("3")
                return False
            if (self.rhymes(rhymeWords[2],rhymeWords[3])) == False :
                #print("4")
                return False
            if (self.rhymes(rhymeWords[0],rhymeWords[2])) == True :
                #print("5")
                return False
            if (self.rhymes(rhymeWords[0],rhymeWords[3])) == True :
                #print("6")
                return False
            if (self.rhymes(rhymeWords[1],rhymeWords[2])) == True :
                #print("7")
                return False
            if (self.rhymes(rhymeWords[1],rhymeWords[3])) == True :
                #print("8")
                return False
            if (self.rhymes(rhymeWords[4],rhymeWords[2])) == True :
                #print("9")
                return False
            if (self.rhymes(rhymeWords[4],rhymeWords[3])) == True :
                #print("10")
                return False
             
        return True
       
#apostrophe_tokenize to match can't and pant  
    def apostrophe_tokenize(self, sentence):
        return_line = []
        words = sentence.split()
        for word in words:
            word = word.lstrip(punctuation)
            word = word.rstrip(punctuation)
        
            return_line.append(word)
        return return_line   
       
#Guess number of syllables for a word      
    def guess_syllables(self, word):
        syllable_count = 0
        word = word.lower()
        if word[0] in ('aeiouy'):
            syllable_count +=  1
        for index, letter in enumerate(word, start=1):
            if index != len(word):
                if word[index] in ('aeiouy') :
                    if word[index-1] not in ('aeiouy'):
                        syllable_count += 1
        
        if word.endswith('e'):
            syllable_count -= 1
        if word.endswith('le'):
            syllable_count +=  1

        return syllable_count
       
# The code below should not need to be modified
def main():
  parser = argparse.ArgumentParser(description="limerick detector. Given a file containing a poem, indicate whether that poem is a limerick or not",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")




  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  ld = LimerickDetector()
  lines = ''.join(infile.readlines())
  outfile.write("{}\n-----------\n{}\n".format(lines.strip(), ld.is_limerick(lines)))

if __name__ == '__main__':
  main()
