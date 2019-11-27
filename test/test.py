#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import pipesubprocess as pipesub
import shlex
import logging
import inspect

class PipesubprocessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=getattr(logging, 'DEBUG', None))

    def setUp(self):
        logging.info("")
        logging.info("**************start**************")
        logging.info("")

    def tearDown(self):
        if self.p:
            self.p.kill()
        logging.info("")
        logging.info("**************end**************")
        logging.info("")

    def get_popen_args_list(self, cmdlist):
        return [pipesub.PopenArgs(shlex.split(cmd)) for cmd in cmdlist]

    def run_popen_basic(self, cmdlist, expected_out):
        popen_args_list = self.get_popen_args_list(cmdlist)
        logging.info([popen_args.args for popen_args in popen_args_list])
        self.p = pipesub.Popen(popen_args_list, text=True, stdout=pipesub.PIPE)
        outs, errs = self.p.communicate()
        outs_line = outs.split('\n')
        if outs_line[-1] == '':
            del outs_line[-1]
        self.assertEqual(outs_line, expected_out)

    def test_001_single(self):
        '''
        Just a single command
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["echo hoge"], ["hoge"])

    def test_002_double_head(self):
        '''
        Two commands piped.
        The last command exits first
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["seq 1 10", "head -1"], ["1"])

    def test_003_double_tail(self):
        '''
        Two commands piped.
        The first command exits first
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["seq 1 10", "tail -1"], ["10"])

    def test_004_triple_head(self):
        '''
        Three commands piped.
        The last command exits first
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["seq 1 10 100", "grep 1", "head -1"], ["1"])

    def test_005_triple_mid(self):
        '''
        Three commands piped.
        The middle command exits first
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["seq 1 10 100", "tail -5", "head -1"], ["51"])

    def test_006_triple_tail(self):
        '''
        Three commands piped.
        The last command exits first
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["seq 1 10 100", "grep 1", "tail -1"], ["91"])

    def test_007_ten_tail(self):
        '''
        Ten commands piped.
        '''
        logging.info(inspect.stack()[0][3])
        self.run_popen_basic(["seq 1 15",
                              "head -10",
                              "head -9",
                              "head -8",
                              "head -7",
                              "head -6",
                              "head -5",
                              "head -4",
                              "head -3",
                              "tail -2"],
                             ["2", "3"])

    def test_008_binarymode(self):
        '''
        Binary data piped
        '''
        logging.info(inspect.stack()[0][3])
        cmdlist = ["cat /bin/cat", "head -c 10", "hexdump"]
        expected_out = b"0000000 cf fa ed fe 07 00 00 01 03 00                  \n000000a\n"
        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list, stdout=pipesub.PIPE)
        outs, errs = self.p.communicate()
        self.assertEqual(outs, expected_out)


    def test_009_stdin(self):
        logging.info(inspect.stack()[0][3])
        input = "1\n2\n3\n"
        cmdlist = ["head -2", "tail -1"]
        expected_out = "2\n"
        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list, text=True, stdout=pipesub.PIPE, stdin=pipesub.PIPE)
        outs, errs = self.p.communicate(input=input)
        self.assertEqual(outs, expected_out)

    def test_010_wait(self):
        logging.info(inspect.stack()[0][3])
        cmdlist = ["sleep 10"]

        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list, text=True, stdout=pipesub.PIPE, stdin=pipesub.PIPE)
        import subprocess
        with self.assertRaises(subprocess.TimeoutExpired):
            self.p.wait(timeout=0.1)

    def test_011_stderr_single(self):
        logging.info(inspect.stack()[0][3])
        cmdlist = ["ls hogehogehoge"]
        expected_out = "ls: hogehogehoge: No such file or directory\n"
        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list, stdout=pipesub.PIPE,
                                stderr=pipesub.PIPE, text=True)
        outs, errs = self.p.communicate()
        self.assertEqual(outs, "")
        self.assertEqual(errs, expected_out)

    def test_012_stderr_multi(self):
        logging.info(inspect.stack()[0][3])
        cmdlist = ["ls hogehogehoge", "ls fugafugafuga", "ls higehigehige"]
        expected_out = ["ls: hogehogehoge: No such file or directory",
                        "ls: fugafugafuga: No such file or directory",
                        "ls: higehigehige: No such file or directory",
                        ""]
        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list, stdout=pipesub.PIPE,
                                stderr=pipesub.PIPE, text=True)
        outs, errs = self.p.communicate()
        self.assertEqual(outs, "")
        self.assertEqual(errs.split("\n"), expected_out)

    def test_013_kill(self):
        logging.info(inspect.stack()[0][3])
        cmdlist = ["sleep 10", "sleep 10", "sleep 10"]
        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list)
        self.p.kill()
        self.assertIsNotNone(self.p.wait(timeout=0))
        self.assertEqual(self.p.returncodes, [-9,-9,-9])

    def test_014_more_than_bufferesize(self):
        logging.info(inspect.stack()[0][3])
        cmdlist = ["dd if=/dev/urandom bs=1048576 count=1",
                   "hexdump"]
        popen_args_list = self.get_popen_args_list(cmdlist)
        self.p = pipesub.Popen(popen_args_list,
                                stdout=pipesub.PIPE,
                                stderr=pipesub.PIPE)
        outs, errs = self.p.communicate()
        self.assertEqual(len(outs), 3670024)
