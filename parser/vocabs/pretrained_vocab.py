#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2016 Timothy Dozat
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import codecs
from collections import Counter

import numpy as np
import tensorflow as tf

import parser.neural.linalg as linalg
from parser.vocabs.base_vocab import BaseVocab

#***************************************************************
class PretrainedVocab(BaseVocab):
  """"""
  
  #=============================================================
  def __init__(self, token_vocab, *args, **kwargs):
    """"""
    
    super(PretrainedVocab, self).__init__(*args, **kwargs)
    
    self._token_vocab = token_vocab
    
    self.load()
    self.count()
    return
  
  #=============================================================
  def __call__(self, placeholder=None, moving_params=None):
    """"""
    
    embeddings = super(PretrainedVocab, self).__call__(placeholder, moving_params=moving_params)
    # (n x b x d') -> (n x b x d)
    with tf.variable_scope(self.name.title()):
      matrix = linalg.linear(embeddings, self.token_embed_size, moving_params=moving_params)
      if moving_params is None:
        with tf.variable_scope('Linear', reuse=True):
          A = tf.get_variable('Weights')
          tf.losses.add_loss(tf.nn.l2_loss(tf.matmul(A, tf.transpose(A)) - tf.eye(self.token_embed_size)))
    return embeddings
  
  #=============================================================
  def load(self):
    """"""
    
    embeddings = []
    start_idx = len(self.special_tokens)
    with codecs.open(self.filename, encoding='utf-8') as f:
      for line_num, line in enumerate(f):
        if line_num < self.max_rank:
          line = line.strip().split(' ')
          embeddings.append(np.array(line[1:], dtype=np.float32))
          self[line[0]] = start_idx + line_num
        else:
          break
    self.embeddings = np.array(embeddings, dtype=np.float32)
    return
  
  #=============================================================
  def count(self):
    """"""
    
    if self.token_vocab is not None:
      zipf = self.token_vocab.fit_to_zipf(plot=False)
      zipf_freqs = zipf.predict(np.arange(len(self))+1)
    else:
      zipf_freqs = -np.log(np.arange(len(self))+1)
    zipf_counts = zipf_freqs / np.min(zipf_freqs)
    for count, token in zip(zipf_counts, self.strings()):
      self.counts[token] = int(count)
    return
  
  #=============================================================
  @property
  def token_vocab(self):
    return self._token_vocab
  @property
  def token_embed_size(self):
    return (self.token_vocab or self).embed_size
  @property
  def embeddings(self):
    return super(PretrainedVocab, self).embeddings
  @embeddings.setter
  def embeddings(self, matrix):
    self._embed_size = matrix.shape[1]
    with tf.device('/cpu:0'):
      with tf.variable_scope(self.name.title()):
        self._embeddings = tf.Variable(matrix, name='Embeddings', trainable=False)
    return

#***************************************************************
if __name__ == '__main__':
  """"""
  
  pretrained_vocab = PretrainedVocab(None)
  print('PretrainedVocab passes')