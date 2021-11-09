from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)


def test_get_entrace_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # ARRANGE
    lottery = deploy_lottery()
    # ACT
    # 4500 eth / usd
    # usdEntryFee is 50
    # 4500/1 == 50/x == 0.011
    excepted_entrance_fee = Web3.toWei(0.011111111111111111, "ether")
    entrace_fee = lottery.getEntranceFee()
    # ASSERT
    assert entrace_fee == excepted_entrance_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # ARRANGE
    lottery = deploy_lottery()
    # ACT/ASSERT
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # ARRANGE
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # ACT
    lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})
    # ASSERT
    assert lottery.players(0) == account


def test_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # ARRAGE
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})
    # ACT
    fund_with_link(lottery.address)
    lottery.endLottery({"from": account})
    # ASSERT
    assert (
        lottery.lottery_state() == 2
    )  # CALCULATING WINNER STATE is in position 2 inside the enum


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # ARRAGE
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})

    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()

    fund_with_link(lottery.address)
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["ReturnRandomness"]["ReturnId"]
    STATIC_RANDOM_NUMBER = 777
    # we can simulate beeing a chainlink node and sending a random number
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RANDOM_NUMBER, lottery.address, {"from": account}
    )

    # we know the winner should be the first entry: 777 % 3 = 0
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
