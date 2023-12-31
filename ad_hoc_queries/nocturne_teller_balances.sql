-- allium.so
-- chart at https://x.com/mud2monarch/status/1741290053228528124?s=20

with all_transfers as (
  select
    b.block_timestamp,
    b.address,
    b.token_symbol,
    b.balance,
    case -- error handling because rETH doesn't have USD price
      when b.usd_balance is null and b.token_symbol = 'rETH'
      then b.balance * e.usd_exchange_rate
      else b.usd_balance
    end as usd_balance
  from ethereum.assets.erc20_balances b
  left join (
    select 
      block_timestamp, 
      avg(usd_exchange_rate) as usd_exchange_rate -- ahhhhhhhhhhhhhhhhh
    from ethereum.assets.erc20_balances
    where token_symbol = 'WETH'
    group by 1
  ) e on b.block_timestamp = e.block_timestamp
  where b.address = '0xa561492dfc1a90418cc8b9577204d56c17cb32ff' -- Teller CA
  and b.block_timestamp >= cast('2023-11-15' as date)
  order by b.block_timestamp desc  
)
select * from all_transfers