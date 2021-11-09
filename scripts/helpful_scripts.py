from brownie import (
    network,
    accounts,
    config,
    MockV3Aggregator,
    LinkToken,
    VRFCoordinatorMock,
    Contract,
    interface,
)

FORKED_LOCAL_ENRIVONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = [
    "development",
    "ganache-local",
]  # this is a list of local networks so that we know when to deploy mocks

DECIMALS = 8
INITIAL_VALUE = 450000000000


def get_account(index=None, id=None):
    # index will choose one of the addresses inside accounts array
    # id will use one of the accounts saved inside brownie -> $ brownie accounts list
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENRIVONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """The function will grab the contract addresses from the brownie config if
    defined, otherwise, it will deploy a mock version of the contract
    and return that mock contract.

        Arg:
            contract_name (string)

        Return:
            brownie.network.contract.ProjectContract: The most recently deployed version of this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
    ):  # check if we are using a local blockchain
        if len(contract_type) <= 0:  # check if mocks have already been deployed
            deploy_mocks()
        contract = contract_type[-1]
    else:  # if you want to deploy to a test net
        contract_address = config["networks"][network.show_active()][contract_name]
        # to interact with a contract on a test net we need the ABI and the address
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})

    print("Deployed Mocks!")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
): # 0.1 link
    
    # the account we use to fund the contract will be an account provided. if not provided we get the default account
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})

    tx.wait(1)
    print("Fund contract!")
    return tx
