with transfers as(
    select
        evt_block_time,
        token_address,
        amount_raw,
        wallet_address
    from transfers_ethereum.erc20
    where token_address in (
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, -- WETH, 18 decimals
        0x6B175474E89094C44Da98b954EedeAC495271d0F, -- DAI, 18 decimals
        0xae78736Cd615f374D3085123A210448E74Fc6393 -- rETH, 18 decimals
        )
        and wallet_address = 0xa561492dfc1a90418cc8b9577204d56c17cb32ff -- Teller CA
    order by 1 desc
),

daily_totals as(
    select
        date_trunc('day', evt_block_time) as day_date,
        token_address,
        sum(cast(amount_raw as double)) as net_change
    from transfers
    group by 1, 2
),

usd_prices as (
    select
        date_trunc('day', minute) as day_date,
        symbol,
        contract_address,
        avg(price) as avg_daily_price
    from prices.usd
    where
        contract_address in (
            0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, -- WETH, 18 decimals
            0x6B175474E89094C44Da98b954EedeAC495271d0F, -- DAI, 18 decimals
            0xae78736Cd615f374D3085123A210448E74Fc6393 -- rETH, 18 decimals
            )
        and minute >= cast('2023-11-15' as date)
        and blockchain = 'ethereum'
    group by 1, 2, 3
    order by 1 asc, 2
),
cum_totals as (
    select
        day_date,
        case
            when token_address = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 then 'WETH' -- WETH, 18 decimals
            when token_address = 0x6B175474E89094C44Da98b954EedeAC495271d0F then 'DAI' -- DAI, 18 decimals
            when token_address = 0xae78736Cd615f374D3085123A210448E74Fc6393 then 'rETH' -- rETH, 18 decimals
            else cast(token_address as varchar(4))
        end as token,
        (sum(net_change) over (partition by token_address order by day_date))/10e17 as total
    from daily_totals
    order by 1 desc
)
select
    c.day_date,
    c.token,
    c.total as total_native,
    p.avg_daily_price,
    c.total * p.avg_daily_price as total_usd
from cum_totals c left join usd_prices p 
    on c.day_date = p.day_date
    and c.token = cast(p.symbol as varchar(4)) -- lmaooooo please work
order by 1 desc, 2