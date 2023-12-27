-- on Dune
-- What is the distribution of wallets vs. no. of transactions for Uniswap v3 on Arbitrum vs Ethereum?
with txn_counts as (
    select
        blockchain,
        tx_from,
        count(tx_hash) as no_of_txns
    from dex.trades
    where blockchain in ('ethereum', 'arbitrum')
        and version = '3'
        and project = 'uniswap'
        and block_date > cast('2023-11-01' as date) and block_date < cast('2023-12-25' as date)
    group by 1, 2
    order by 3 desc
),

txn_percentiles as (
    select 
        blockchain,
        approx_percentile(no_of_txns, 0.9999) as p99_99_txn_count,
        approx_percentile(no_of_txns, 0.999) as p99_9_txn_count,
        approx_percentile(no_of_txns, 0.99) as p99_txn_count,
        approx_percentile(no_of_txns, 0.9) as p90_txn_count,
        approx_percentile(no_of_txns, 0.5) as median_txn_count,
        approx_percentile(no_of_txns, 0.1) as p10_txn_count
    from txn_counts
    group by 1
    order by 2 desc
)

-- can decide what to pull here!
select *
from txn_counts
where no_of_txns >= 40