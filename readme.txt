Ispell dictionary for galician ("mínimos" standar) 
--------------------------------------------------

This a ispell dictionary for galician, using the "mínimos" standar. It's
freely available under the terms of the GNU GPL. You can freely
redistribute and/or use it for spell checking with the program ispell 	
		
	http://fmg-www.cs.ucla.edu/ficus-members/geoff/ispell.html. 

The main page for this dictionary is
	http://ispell-gl.sourceforge.net/
	

This dictionary uses both upper- and lower-case affix flags, and 8 bits
(latin1). So ispell must be compiled taking this into account, in your
local.h file 

	  include: #define MASKBITS 64   
and	  remove:  #define NO8BIT 

Nowaday most of the binary versions of ispell are compiled in this way.


AVAILABLE MODES

	-T lat	  (latin1, i.e. á, é, ñ ...)
	-T tex	  (tex, i.e. \'a, \'e, \~n ...)
	-T pre	  (nroff, i.e. 'a, 'e, 'i ...)



Any comments, important new words, and errors should be mailed to
Ramón Flores <fa2ramon@usc.es>
