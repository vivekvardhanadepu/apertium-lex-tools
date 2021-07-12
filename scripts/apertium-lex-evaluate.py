#!/usr/bin/python3
# coding=utf-8
# -*- encoding: utf-8 -*-

import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('src', help='output of translator up to lt-proc -b')
parser.add_argument('ref', help='reference corpus')
parser.add_argument('tst', help='output of lexical selection module')
parser.add_argument('-d', '--debug', action='store_true')
parser.add_argument('-q', '--quiet', action='store_true')
parser.add_argument('-l', '--line', action='store_true')
args = parser.parse_args()

def debug(msg):
	global args
	if args.debug:
		print(msg, file=sys.stderr)

f_src = open(args.src)
f_ref = open(args.ref)
f_tst = open(args.tst)

def lineToArray(line):
	current_word_sl = ''
	current_word_tl = ''
	current_words_tl = []
	firstWord = False
	inWord = False
	lus = []

	for c in line:
		if c == '^':
			inWord = True
			firstWord = True
			continue
		elif c == '$':
			current_words_tl.append(current_word_tl)
			current_word = (current_word_sl, current_words_tl)
			lus.append(current_word)
			current_word_sl = ''
			current_word_tl = ''
			current_words_tl = []
			i = 0
			inWord = False
			continue
		elif c == '/':
			if firstWord:
				firstWord = False
			else:
				current_words_tl.append(current_word_tl)
				current_word_tl = ''
			continue

		if inWord and firstWord:
			current_word_sl = current_word_sl + c
		elif inWord and not firstWord:
			current_word_tl = current_word_tl + c

	return lus

def sanityChecks(l_src, l_ref, l_tst):
	debug('---')
	src_lu = []
	ref_lu = []
	tst_lu = []

	src_lu = lineToArray(l_src)
	ref_lu = lineToArray(l_ref)
	tst_lu = lineToArray(l_tst)

	debug('src: %s' % src_lu)
	debug('tst: %s' % tst_lu)
	debug('ref: %s' % ref_lu)

	if len(src_lu) != len(ref_lu):
		print('WARNING: Source and reference sentence have different number of lexical units.', file=sys.stderr)
		print('SRC: ' , len(src_lu) , ": " + l_src, file=sys.stderr)
		print('REF: ' , len(ref_lu) , ": " + l_ref, file=sys.stderr)


	if len(src_lu) != len(tst_lu):
		print('WARNING: Source and test sentence have different number of lexical units.', file=sys.stderr)
		print(len(src_lu) , ": " + l_src, file=sys.stderr)
		print(len(tst_lu) , ": " + l_tst, file=sys.stderr)


#       i) do a sanity check, look for outN in tst that aren't in src: LEX module is outputting strange stuff

	for i in range(0, len(tst_lu)):
		if len(tst_lu[i][1]) > 1:
			print('WARNING: Test sentence has a translation with more than one option.', file=sys.stderr)
			print('        ',src_lu[i], file=sys.stderr)
			print('        ',ref_lu[i], file=sys.stderr)
			print('        ',tst_lu[i][1], file=sys.stderr)

		for lu in tst_lu[i][1]:
			if lu not in src_lu[i][1]:
				print('WARNING: Test sentence has a translation option that can never ', file=sys.stderr)
				print(' be generated by the MT system.', file=sys.stderr)
				print('        TST: ', tst_lu[i], file=sys.stderr)
				print('        SRC: ', src_lu[i], file=sys.stderr)




#      ii) look for outN in ref that aren't in src: MT system has changed

	for i in range(0, len(ref_lu)):
		for lu in ref_lu[i][1]:
			if lu not in src_lu[i][1]:
				print('WARNING: Reference sentence has a translation option that can never ', file=sys.stderr)
				print(' be generated by the MT system.', file=sys.stderr)
				print('REF: ', ref_lu[i], file=sys.stderr)
				print('SRC: ', src_lu[i], file=sys.stderr)

	return (src_lu, ref_lu, tst_lu)


# Process:
#  Read linestep, for each line in the three files:
#    1) read into arrays src[0] = (in, [out1, out2]) , etc.
#    2)
#       i) do a sanity check, look for outN in tst that aren't in src: LEX module is outputting strange stuff
#      ii) look for outN in ref that aren't in src: MT system has changed
#     iii) look for unambiguous words in src that have a different TL translation than in ref.
#    3)
#       i) for each of the lines,
#      ii)    for each of LUs,
#     iii)        for each of the TL possibilities: check to see if it is in the ref
#      iv)            if it is in the ref, increase score for that LU by 1.
#       v)        final score is number of good TL translations / total number of TL translations

lines = True

lineno = 0

total_ambig_lus = 0
total_fallos = 0

while lines:

	l_src = f_src.readline()
	l_ref = f_ref.readline()
	l_tst = f_tst.readline()

	if l_src.strip('[]') == '' and l_ref.strip('[]') == '' and l_tst.strip('[]') == '':
		lines = False
		continue

	lineno = lineno + 1

	(lu_src, lu_ref, lu_tst) = sanityChecks(l_src, l_ref, l_tst)

	num_ambig_lus = 0
	num_fallos = 0

	for i in range(0, len(lu_tst)):
		#  We are only interested in counting a mismatch as an error if the
		#  source LU has more than one possible translation, and
		#  the number of translations is lower in the reference. This means
		#  that if we have two possible translations in both the source and
		#  the reference, it should not be considered ambiguous as both are
		#  valid.
		if len(lu_src[i][1]) > 1 and len(lu_ref[i][1]) != len(lu_src[i][1]) and lu_ref[i][1] != lu_src[i][1]:
#			>> 2 3 station<n><sg> [u'station<n><sg>'] +++ [u'station<n><sg>', u'season<n><sg>', u'ski resort<n><sg>']
#			XX station<n><sg> XX  [u'station<n><sg>']

			num_ambig_lus = num_ambig_lus + 1
			debug('>> %s %s %s +++' % (len(lu_tst[i][1]), len(lu_src[i][1]),
									   lu_tst[i][1][0], lu_ref[i][1],
									   lu_src[i][1]))
			debug('XX %s XX  %s' % (lu_tst[i][1][0], lu_ref[i][1]))
			if lu_tst[i][1][0] not in lu_ref[i][1]:
				num_fallos = num_fallos + 1
				debug('MISMATCH: %s not in %s' % (lu_tst[i][1][0], lu_ref[i][1]))




	if num_fallos == 0 and num_ambig_lus == 0:
#		print('WEIRD: ' , l_src)
#		print('     : ' , l_ref)
#		print('     : ' , l_tst)
		continue

	err = float(num_fallos)/float(num_ambig_lus)*100
	errh = str(err).split('.')[0]
	errt = ''.join(str(err).split('.')[1][0:1])
	if args.line:
		print(n_tst + ':' + str(lineno) + ' ' + str(num_fallos) + '/' + str(num_ambig_lus) + ' ' + errh + '.' + errt + '%')

	total_ambig_lus = total_ambig_lus + num_ambig_lus
	total_fallos = total_fallos + num_fallos


if total_fallos == 0 or total_ambig_lus == 0:
	print('what: ' , total_fallos ,total_ambig_lus)
	print("Check you haven't tried to use the source as a reference")

err = float(total_fallos)/float(total_ambig_lus)*100
errh = str(err).split('.')[0]
errt = ''.join(str(err).split('.')[1][0:1])
#print(n_tst + ' ' + str(total_fallos) + '/' + str(total_ambig_lus) + ' ' + errh + '.' + errt + '%')
if args.quiet:
	print(errh + '.' + errt)
else:
	print(str(total_fallos) + '/' + str(total_ambig_lus) + '\t' + errh + '.' + errt + '%')
