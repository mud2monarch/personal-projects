# Guest Lecture Lesson Plan

Below is a suggested outline for walking your class through the sample Jupyter notebook. The notebook’s cells are labeled in a logical order, and here we provide talking points for each step.

---

### Cell 1: Overview
- **What happens here?**  
  A Markdown introduction to the goals of this demo: generating a wallet, obtaining ETH, wrapping it into WETH, approving the router, and swapping.

- **Talking point**: Highlight for students how DeFi tooling (like `web3.py`) allows direct programmatic interaction with contracts—no broker or centralized intermediary.

---

### Cell 2: Imports and Environment Setup
- **What happens here?**  
  - We import `web3.py`, `eth_account`, `dotenv`, etc.
  - We instantiate a `Web3` object connected to our **Unichain Sepolia** testnet RPC URL.

- **Talking point**: In traditional finance, there’s a bank or a “financial institution” as the central ledger keeper. Here, we’re simply connecting to a public RPC endpoint that any participant can run.

---

### Cell 3: Generate a New Wallet
- **What happens here?**
  - We create a random private key using Python’s `secrets` library.
  - We derive the public address for that private key.

- **Talking point**: Emphasize that in blockchains, anyone can generate as many wallets as they like. There’s no KYC process on the protocol level. This is *fundamentally different* from how accounts are created at a traditional financial institution.

---

### Cell 4: Fund the New Wallet
- **What happens here?**
  - Just a Markdown cell reminding you to send test ETH from another wallet or faucet.

- **Talking point**: This step is analogous to “funding” a new bank account, but we do it self-service by sending testnet ETH from an existing wallet. Again, no intermediaries or forms; you just need the address and the chain’s native asset.

---

### Cell 5: Confirm Wallet Balance
- **What happens here?**
  - We check our address’s ETH balance.

- **Talking point**: In traditional finance, you’d likely check your balance by logging into the bank’s web portal. Here, you just query the public blockchain data. `web3.py` is merely reading from the distributed ledger.

---

### Cell 6–7: Wrap ETH into WETH
- **What happens here?**
  - We call `deposit()` on the WETH contract with some ETH (`value` in the transaction).
  - We confirm how many WETH tokens we now have.

- **Talking point**: WETH is just an ERC-20 token that represents ETH 1:1. Wrapping allows tokens to abide by the “ERC-20” standard, so they can be seamlessly used in smart contracts like Uniswap. This concept doesn’t exist in TradFi.

---

### Cell 8–9: Approve the SwapRouter to Spend WETH
- **What happens here?**
  - We call the `approve` function on the WETH contract, giving the Uniswap router permission (an allowance) to spend our WETH.
  - We check that the allowance is properly set.

- **Talking point**: This is a major conceptual difference vs. traditional financial rails. Each user must explicitly “approve” a contract to move tokens on their behalf. This design choice stems from how ERC-20 tokens are managed on decentralized ledgers.

---

### Cell 10: Swap WETH for USDC
- **What happens here?**
  - We build a transaction using the Uniswap V3 SwapRouter’s `exactInputSingle()` function.  
  - We specify WETH → USDC, a fee tier, and an amount to swap.

- **Talking point**:  
  - Normally, in TradFi, a swap or currency exchange is done through an intermediary (bank or FX broker). Here, we invoke a smart contract directly.  
  - The transaction includes all the logic needed for the swap on-chain. No “middle person” is needed.

---

### Cell 11–12: Verify Final Balances
- **What happens here?**
  - We read back how much WETH remains and how much USDC we received.

- **Talking point**:  
  - The final check is a public ledger query—no central database.  
  - The demonstration helps show that once you have block explorer / chain-level knowledge, the entire transaction flow is verifiable by anyone.

---

## Broader Regulatory Discussion

- **Key difference**: Financial services on a blockchain have no “custodial” middle layer. Users interface directly with self-executing code.  
- **Implication**: Existing regulations often assume an identifiable intermediary (e.g., broker-dealer, bank) with compliance responsibilities. Smart contracts complicate that assumption.  
- **Open question**: Should (or can) regulators treat *decentralized* code-based services differently from traditional, intermediated providers?  

End with a Q&A on how these fundamental differences in structure might affect policy choices and regulatory frameworks.
