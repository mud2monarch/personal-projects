select
    evt_tx_from,
    evt_tx_to,
    value/pow(10,18) as value,
    evt_block_number
from erc20_base.evt_transfer
where contract_address in (
    0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10, --AR
    0x20ef84969f6d81Ff74AE4591c331858b20AD82CD, --AiSTR
    0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D --ALCH
    )
    and evt_tx_to not in (
    0x197ecb5c176aD4f6e77894913a94c5145416f148, -- AiSTR/WETH 1%
    0xF5677B22454dEe978b2Eb908d6a17923F5658a79, -- ALCH/WETH 1%
    0x3fdD9A4b3CA4a99e3dfE931e3973C2aC37B45BE9 -- AR/WETH 1%
    )
    and evt_block_number <= 24223297 -- Dec. 26, 12:59 PM ET