from brownie import accounts, Lottery, network, config
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
import time


def deploy_lottery():
    account = get_account()  # id="accountKovaEnrico"
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Deployed lottery!")
    return lottery


def strat_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("The lottery is started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = (
        lottery.getEntranceFee() + 100000000
    )  # add 0.00004 usd just to be sure, sometimes can be off by a few wei.
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # fund the contract
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    # end the lottery
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    # wait for the chainlink node to respond
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    deploy_lottery()
    strat_lottery()
    enter_lottery()
    end_lottery()
