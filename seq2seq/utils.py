import mxnet as mx
import re
import operator
import string
from unidecode import unidecode
from collections import defaultdict
from time import time
from collections import namedtuple
from tqdm import tqdm

Dicts = namedtuple(
    'Dicts',
    ['src_vocab', 'inv_src_vocab', 'targ_vocab', 'inv_targ_vocab'])

Dataset = namedtuple(
    'Dataset',
    ['src_train_sent', 'src_valid_sent', 'src_vocab', 'inv_src_vocab', 
     'targ_train_sent', 'targ_valid_sent', 'targ_vocab', 'inv_targ_vocab'])


def invert_dict(d):
    return {v: k for k, v in d.iteritems()}

def encode_sentences(sentences, vocab):
    res = []
    for sent in sentences:
        coded = []
        for word in sent:
            coded.append(vocab[word])
        res.append(coded)
    return res 

def preprocess_lines(fname):
    print("Reading file: %s" % fname)
    lines = unidecode(open(fname).read().decode('utf-8')).split('\n')
    lines = map(lambda x: filter(lambda y: y != '', re.sub('\s+', ' ', re.sub('([' + string.punctuation + '])', r' \1 ', x) ).split(' ')), lines)
    lines = filter(lambda x: x != [], lines)
    return lines

def word_count(lines, data_name=''):
    counts = defaultdict(long)
    for line in tqdm(lines, desc='word count (%s)' % data_name):
        for word in line:
            counts[word] += 1
    return counts

def merge_counts(dict1, dict2):
    return { k: dict1.get(k, 0) + dict2.get(k, 0) for k in tqdm(set(dict1) | set(dict2), desc='merge word counts') }

def top_words_train_valid(train_fname, valid_fname, top_k=1000, unk_key=0, reserved_tokens=['<UNK>', '<PAD>', '<EOS>', '<GO>']):

    counts = word_count(preprocess_lines(train_fname), data_name='train')
#    valid_counts = word_count(preprocess_lines(valid_fname), data_name='valid')
#    counts   = merge_counts(train_counts, valid_counts)

    print("Choosing top n words for the dictionary.")
    sorted_x = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
    sorted_x = map(lambda x: x[0], sorted_x[:top_k]) # sorted_x
    start_idx = len(reserved_tokens)
    sorted_x = zip(sorted_x, range(start_idx, len(sorted_x) + start_idx))
    # value 0 is reserved for <UNK> or its semantic equivalent
    tops = defaultdict(lambda: 0, sorted_x)

    for i in range(len(reserved_tokens)):
        tops[reserved_tokens[i]] = i

    inv_tops = invert_dict(tops)
    inv_tops[unk_key] = '<UNK>'
    return tops, inv_tops

def tokenize_text(path, vocab):
    lines = preprocess_lines(path)
    print("Encoding sentences")
    sentences = encode_sentences(lines, vocab)
    return sentences, vocab

def array_to_text(array, inv_vocab):
    sent = []
    for token in array:
        sent.append(inv_vocab[token])
    return " ".join(sent)

def get_s2s_data(src_train_path, src_valid_path, targ_train_path, targ_valid_path,
         reserved_tokens=['<UNK>', '<PAD>', '<EOS>', '<GO>']):

        print("Creating joint source dictionary")
        src_dict, inv_src_dict = top_words_train_valid(src_train_path, src_valid_path)
       
        print("Tokenizing src_train_path") 
	src_train_sent, _ = tokenize_text(src_train_path, vocab=src_dict)
        print("Tokenizing targ_train_path")
        src_valid_sent, _ = tokenize_text(src_valid_path, vocab=src_dict)

        print("Creating joint target dictionary")
        targ_dict, inv_targ_dict = top_words_train_valid(targ_train_path, targ_valid_path)

        print("Tokenizing targ_train_path")
	targ_train_sent, _ = tokenize_text(targ_train_path, vocab=targ_dict)
        print("Tokenizing targ_valid_path")
        targ_valid_sent, _ = tokenize_text(targ_valid_path, vocab=targ_dict)

        print("\nEncoded examples:\n")
        for i in range(5):
            print(array_to_text(src_train_sent[i], inv_src_dict))            

	return Dataset(
		src_train_sent=src_train_sent, src_valid_sent=src_valid_sent, src_vocab=src_dict, inv_src_vocab=inv_src_dict,
		targ_train_sent=targ_train_sent, targ_valid_sent=targ_valid_sent, targ_vocab=targ_dict, inv_targ_vocab=inv_targ_dict)

