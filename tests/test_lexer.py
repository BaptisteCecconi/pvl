#!/usr/bin/env python
"""This module has new tests for the pvl decoder functions."""

# Copyright 2019, Ross A. Beyer (rbeyer@seti.org)
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

import unittest

from pvl.grammar import grammar as Grammar

import pvl.lexer as Lexer


class TestInternal(unittest.TestCase):

    def test_prev_char(self):
        self.assertIsNone(Lexer._prev_char('foo', 0))
        self.assertEqual('f', Lexer._prev_char('foo', 1))

    def test_next_char(self):
        self.assertIsNone(Lexer._next_char('foo', 2))
        self.assertEqual('b', Lexer._next_char('fob', 1))

    def test_prepare_comment_tuples(self):
        d = dict(single_comments=dict(),
                 multi_chars=set('/*'),
                 chars=set('/*'))
        self.assertEqual(d, Lexer._prepare_comment_tuples((('/*', '*/'),)))

        d = dict(single_comments={'#': '\n'},
                 multi_chars=set('/*'),
                 chars=set('/*#'))
        self.assertEqual(d, Lexer._prepare_comment_tuples((('/*', '*/'),
                                                          ('#', '\n'))))


class TestLexComments(unittest.TestCase):

    def test_lex_multichar_comments(self):
        self.assertEqual(('', False, None),
                         Lexer.lex_multichar_comments('a', 'b', 'c',
                                                      '', False, None))
        self.assertEqual(('', False, None),
                         Lexer.lex_multichar_comments('/', '*', 'c',
                                                      '', False, None))
        self.assertEqual(('', False, None),
                         Lexer.lex_multichar_comments('/', 'b', '*',
                                                      '', False, None))
        self.assertEqual(('/', False, None),
                         Lexer.lex_multichar_comments('/', 'b', 'c',
                                                      '', False, None))
        self.assertEqual(('*', True, None),
                         Lexer.lex_multichar_comments('*', 'b', 'c',
                                                      '', True, None))
        self.assertEqual(('/*', True, None),
                         Lexer.lex_multichar_comments('*', '/', 'c',
                                                      '', False, None))
        self.assertEqual(('*/', False, None),
                         Lexer.lex_multichar_comments('*', 'c', '/',
                                                      '', True, None))

        self.assertRaises(ValueError,
                          Lexer.lex_multichar_comments, 'a', 'b', 'c',
                          '', False, None, tuple())
        self.assertRaises(NotImplementedError,
                          Lexer.lex_multichar_comments, 'a', 'b', 'c',
                          '', False, None, (('/*', '*/'), ('#', '\n')))

    def test_lex_singlechar_comments(self):
        self.assertEqual(('', False, 'end'),
                         Lexer.lex_singlechar_comments('a', '', False, 'end',
                                                       {'k': 'v'}))
        self.assertEqual(('#', True, '\n'),
                         Lexer.lex_singlechar_comments('#', '', False, 'end',
                                                       {'#': '\n'}))
        self.assertEqual(('#\n', False, None),
                         Lexer.lex_singlechar_comments('\n', '#', True, '\n',
                                                       {'#': '\n'}))

    def test_lex_comment(self):
        self.assertEqual(('', False, 'end'),
                         Lexer.lex_comment('a', 'b', 'c',
                                           '', False, 'end',
                                           (('/*', '*/'),),
                                           dict(single_comments={'k': 'v'},
                                                multi_chars=set(('/', '*')))))

        self.assertEqual(('/*', True, None),
                         Lexer.lex_comment('*', '/', 'c',
                                           '', False, None,
                                           (('/*', '*/'),),
                                           dict(single_comments={'k': 'v'},
                                                multi_chars=set(('/', '*')))))


class TestLexer(unittest.TestCase):

    def setUp(self):
        def get_tokens(s):
            tokens = list()
            lex = Lexer.lexer(s)
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        self.get_tokens = get_tokens

    def test_plain(self):
        s = 'This is a test.'
        tokens = s.split()
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_newline(self):
        s = 'This \n is  a\ttest.'
        tokens = ['This', 'is', 'a', 'test.']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_reserved(self):
        s = 'Te=st'
        tokens = ['Te', '=', 'st']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_comment(self):
        s = 'There is a /* comment */'
        tokens = ['There', 'is', 'a', '/* comment */']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

        s = '/* At */ the beginning'
        tokens = ['/* At */', 'the', 'beginning']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

        s = 'In/*the*/middle.'
        tokens = ['In', '/*the*/', 'middle.']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_custom_comment(self):
        def get_tokens(s):
            tokens = list()
            g = Grammar()
            g.comments = (('/*', '*/'), ('#', '\n'))
            lex = Lexer.lexer(s, g=g)
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        s = 'There is a # comment'
        tokens = ['There', 'is', 'a', '# comment']
        out = get_tokens(s)
        self.assertEqual(tokens, out)

        s = 'There is a # comment \n then more'
        tokens = ['There', 'is', 'a', '# comment \n', 'then', 'more']
        out = get_tokens(s)
        self.assertEqual(tokens, out)

        s = '# Leading \n then \n more'
        tokens = ['# Leading \n', 'then', 'more']
        out = get_tokens(s)
        self.assertEqual(tokens, out)

    def test_numeric(self):
        s = 'Number: +79'
        tokens = ['Number:', '+79']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_send(self):
        s = "One Two Three"
        tokens = Lexer.lexer(s)
        for t in tokens:
            if t == "Two":
                tokens.send(t)  # return the Token to the generator
                break

        self.assertEqual("Two", next(tokens))

    def test_lex_char(self):
        g = Grammar()
        self.assertEqual(('a', False, 'end'),
                         Lexer.lex_char('a', 'b', 'c',
                                        '', False, 'end',
                                        g,
                                        dict(chars=set(['k', 'v', '/', '*']),
                                             single_comments={'k': 'v'},
                                             multi_chars=set(('/', '*')))))

    def test_lexer_recurse(self):

        def foo(tokens):
            two = list()
            for t in tokens:
                if t == 'f':
                    break
                two.append(t)
            return two

        lex = Lexer.lexer('a b c d e f g h')
        one = list()
        for t in lex:
            if t == 'c':
                two = foo(lex)
            else:
                one.append(t)

        self.assertEqual(['a', 'b', 'g', 'h'], one)
        self.assertEqual(['d', 'e'], two)
