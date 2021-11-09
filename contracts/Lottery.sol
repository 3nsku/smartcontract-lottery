// SPDX-License-Identifier: MIT

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

pragma solidity ^0.8.0;

contract Lottery is VRFConsumerBase, Ownable {
    AggregatorV3Interface internal ethUsdPriceFeed;
    address payable[] public players;
    address payable public recentWinner;
    uint256 public randomness;
    uint256 public usdEntryFee = 50 * (10**18); //convert to wei
    uint256 public fee;
    bytes32 public keyHash;

    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;
    event ReturnRandomness(bytes32 ReturnId);

    constructor(
        address _priceFeedAddressEthUsd,
        address _vrfCordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) VRFConsumerBase(_vrfCordinator, _link) {
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddressEthUsd);
        lottery_state = LOTTERY_STATE.CLOSED; //YOU CAN ALSO DO lottery_state = 1
        fee = _fee;
        keyHash = _keyHash;
    }

    function enter() public payable {
        //require $50
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not Enough ETH!");
        players.push(payable(msg.sender));
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        uint256 AjustedPrice = uint256(price) * 10**10; //convert to uint256 and multiply by 18 decimals.
        uint256 costToEnter = (usdEntryFee * 10**18) / AjustedPrice;

        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER; //no one can enter the lotter while we are calculating the winner.

        bytes32 requestId = requestRandomness(keyHash, fee); //will return a byte23 request id
        
        emit ReturnRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You are not there yet!"
        );
        require(_randomness > 0, "Random not found");

        //pick a random winner out of our list of players
        uint256 IndexOfWinner = _randomness % players.length;

        recentWinner = players[IndexOfWinner];

        //transfer all the lottery entries to the winner
        recentWinner.transfer(address(this).balance);

        //reset the lottery
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
