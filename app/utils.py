from flask import Flask, jsonify
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from spl.token.instructions import create_mint, create_associated_token_account, mint_to, revoke

app = Flask(__name__)

# Solana cluster URL
SOLANA_URL = "https://api.devnet.solana.com"

# Token details
DECIMALS = 9
MINT_AMOUNT = 1000000

@app.route('/create_token', methods=['POST'])
def create_token():
    # Create a new Solana keypair for the token mint
    mint_keypair = Keypair.generate()
    mint_pubkey = mint_keypair.public_key

    # Create a new Solana keypair for the token account
    token_keypair = Keypair.generate()
    token_pubkey = token_keypair.public_key

    owner_keypair = Keypair.generate()
    private_key = owner_keypair.secret_key
    # Connect to the Solana cluster
    client = Client(SOLANA_URL, private_key=owner_keypair)

    # Get the minimum balance for rent exemption
    min_balance = client.get_minimum_balance_for_rent_exemption(82)

    print("Private Key:", private_key)
    
    # Create the token mint transaction
    mint_tx = Transaction().add(
        create_mint(
            payer=PublicKey(client.get_default_signer().public_key),
            mint=mint_pubkey,
            decimals=DECIMALS,
            mint_authority=PublicKey(client.get_default_signer().public_key),
            freeze_authority=PublicKey(client.get_default_signer().public_key),
        )
    )

    # Create the associated token account transaction
    token_tx = Transaction().add(
        create_associated_token_account(
            payer=PublicKey(client.get_default_signer().public_key),
            associated_token=token_pubkey,
            owner=PublicKey(client.get_default_signer().public_key),
            mint=mint_pubkey,
        )
    )

    # Mint tokens to the associated token account
    mint_to_tx = Transaction().add(
        mint_to(
            mint=mint_pubkey,
            destination=token_pubkey,
            amount=MINT_AMOUNT,
            authority=PublicKey(client.get_default_signer().public_key),
        )
    )

    # Revoke the freeze authority
    revoke_freeze_tx = Transaction().add(
        revoke(
            account=mint_pubkey,
            authority=PublicKey(client.get_default_signer().public_key),
            authority_type="FreezeAccount",
        )
    )

    # Revoke the mint authority
    revoke_mint_tx = Transaction().add(
        revoke(
            account=mint_pubkey,
            authority=PublicKey(client.get_default_signer().public_key),
            authority_type="MintTokens",
        )
    )

    # Send and confirm the transactions
    mint_result = client.send_transaction(mint_tx, mint_keypair)
    token_result = client.send_transaction(token_tx, token_keypair)
    mint_to_result = client.send_transaction(mint_to_tx)
    revoke_freeze_result = client.send_transaction(revoke_freeze_tx)
    revoke_mint_result = client.send_transaction(revoke_mint_tx)

    # Wait for the transactions to be confirmed
    client.confirm_transaction(mint_result["result"])
    client.confirm_transaction(token_result["result"])
    client.confirm_transaction(mint_to_result["result"])
    client.confirm_transaction(revoke_freeze_result["result"])
    client.confirm_transaction(revoke_mint_result["result"])

    # Get the Solscan links for the transactions
    mint_link = f"https://solscan.io/tx/{mint_result['result']}"
    token_link = f"https://solscan.io/tx/{token_result['result']}"
    mint_to_link = f"https://solscan.io/tx/{mint_to_result['result']}"
    revoke_freeze_link = f"https://solscan.io/tx/{revoke_freeze_result['result']}"
    revoke_mint_link = f"https://solscan.io/tx/{revoke_mint_result['result']}"

    

    return jsonify({
        "mint_pubkey": str(mint_pubkey),
        "token_pubkey": str(token_pubkey),
        "mint_link": mint_link,
        "token_link": token_link,
        "mint_to_link": mint_to_link,
        "revoke_freeze_link": revoke_freeze_link,
        "revoke_mint_link": revoke_mint_link,
    })

if __name__ == '__main__':
    app.run()