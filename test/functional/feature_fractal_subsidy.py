#!/usr/bin/env python3
# Copyright (c) 2026 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Verify Fractal FIP-102 templates and excessive-coinbase rejection.

Regtest uses a 150-block halving interval. The first boundary must reduce
25 FB directly to 6.25 FB, with normal halvings thereafter. No wallet,
external peers, or production chain data are required.
"""

from test_framework.blocktools import create_block, create_coinbase
from test_framework.messages import COIN, COutPoint, CTransaction, CTxIn, CTxOut
from test_framework.script import CScript, OP_TRUE
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class FractalSubsidyTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def template(self, height, subsidy):
        template = self.nodes[0].getblocktemplate({"rules": ["segwit"]})
        assert_equal(template["height"], height)
        assert_equal(template["transactions"], [])
        assert_equal(template["coinbasevalue"], subsidy)
        return template

    def block(self, template, coinbase_value, transactions=None):
        coinbase = create_coinbase(template["height"], nValue=25)
        coinbase.vout[0].nValue = coinbase_value
        coinbase.rehash()
        block = create_block(coinbase=coinbase, tmpl=template, txlist=transactions)
        block.solve()
        return block

    def accept(self, block):
        node = self.nodes[0]
        assert_equal(node.submitblock(block.serialize().hex()), None)
        assert_equal(node.getbestblockhash(), block.hash)

    def reject(self, block):
        node = self.nodes[0]
        old_tip = node.getbestblockhash()
        assert_equal(node.submitblock(block.serialize().hex()), "bad-cb-amount")
        assert_equal(node.getbestblockhash(), old_tip)

    def check_boundary(self, height, subsidy):
        template = self.template(height, subsidy)
        self.reject(self.block(template, subsidy + 1))
        block = self.block(template, subsidy)
        self.accept(block)
        return block

    def run_test(self):
        node = self.nodes[0]
        assert_equal(node.getnetworkinfo()["version"], 400)

        self.log.info("Check height-one allocation and prepare a mature coinbase")
        self.accept(self.block(self.template(1, 105_000_000 * COIN), 105_000_000 * COIN))
        funding = self.block(self.template(2, 25 * COIN), 25 * COIN)
        self.accept(funding)
        self.generate(node, 146)

        self.log.info("Check the last 25 FB block and first 6.25 FB block")
        self.check_boundary(149, 25 * COIN)
        template = self.template(150, 625_000_000)
        # The obsolete v0.3.0 reward must be rejected, even with valid PoW.
        self.reject(self.block(template, 1_250_000_000))
        self.reject(self.block(template, 625_000_001))

        # Include real fees from a mature anyone-can-spend coinbase. Check the
        # allowed subsidy + fees, not just an empty-block subsidy comparison.
        fee = 12_345
        spend = CTransaction()
        spend.vin = [CTxIn(COutPoint(funding.vtx[0].sha256, 0))]
        spend.vout = [CTxOut(25 * COIN - fee, CScript([OP_TRUE]))]
        spend.rehash()
        self.reject(self.block(template, 625_000_000 + fee + 1, [spend]))
        self.accept(self.block(template, 625_000_000 + fee, [spend]))
        self.check_boundary(151, 625_000_000)

        self.log.info("Check that later boundaries halve normally")
        self.generate(node, 147)
        self.check_boundary(299, 625_000_000)
        self.check_boundary(300, 312_500_000)
        self.check_boundary(301, 312_500_000)


if __name__ == '__main__':
    FractalSubsidyTest(__file__).main()
