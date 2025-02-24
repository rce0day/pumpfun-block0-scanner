import requests
import time

rpc_url = "" # rpc url here, recommend using helius for stability

def get_transaction(tx_hash: str, retry_count: int = 0, max_retries: int = 3) -> dict | None: # fetch transaction from rpc
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            tx_hash,
            {
                "maxSupportedTransactionVersion": 0,
                "encoding": "jsonParsed"
            }
        ]
    }

    try:
        response = requests.post(rpc_url, json=payload)
        result = response.json()
        
        if not result.get('result'):
            if retry_count < max_retries:
                print(f"Transaction not found, retrying in 5 seconds... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(5)
                return get_transaction(tx_hash, retry_count + 1, max_retries)
            return None
        return result['result']
    except Exception as e:
        print(f"Error getting transaction: {e}")
        return None

def extract_tx_info(tx_hash: str) -> tuple[list[str], list[str]]: # extract signers and program ids from transaction
    tx = get_transaction(tx_hash)
    signers = []
    programids = []
    if tx:
        accountkeys = tx['transaction']['message']['accountKeys']
        for accountkey in accountkeys:
            if accountkey["signer"]:
                signers.append(accountkey["pubkey"])
    programid = tx['transaction']['message']['instructions'][0].get('programId', False)
    if programid:
        programids.append(programid)
    return signers, programids

def signature_func(mint: str): # get all txs for mint
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            mint,
            {
                "maxSupportedTransactionVersion": 0,
                "encoding": "jsonParsed"
            }
        ]
    }
    response = requests.post(rpc_url, json=payload)
    result = response.json()
    creation_slot = result['result'][-1]['slot']
    
    creation_txs = 0
    signers_pubkeys = set()
    program_ids = set()
    tx_with_multiple_signers = 0
    
    for i in result['result']:
        if i['slot'] == creation_slot:
            creation_txs += 1
            signers, programids = extract_tx_info(i['signature'])
            if len(signers) > 1:
                tx_with_multiple_signers += 1
            signers_pubkeys.update(signers)
            program_ids.update(programids)

    print("\n" + "="*50)
    print("ANALYSIS RESULTS")
    print("="*50 + "\n")

    print("UNIQUE SIGNERS:")
    for signer in sorted(signers_pubkeys):
        print(f"  • {signer}")
    
    print("\nPROGRAM IDs:")
    for prog_id in sorted(program_ids):
        print(f"  • {prog_id}")

    print("\nSTATISTICS:")
    print(f"  • Total Unique Signers: {len(signers_pubkeys)}")
    print(f"  • Total Unique Programs: {len(program_ids)}")
    print(f"  • Transactions with Multiple Signers: {tx_with_multiple_signers}")
    print("\n" + "="*50 + "\n")

    if tx_with_multiple_signers > 0:
        print("Block-0 Method Detected")

signature_func("BPUwso61kETGSpkP8LLBWXE78a9Gxtnxm1DZWK9qpump") # example mint, input rpc at the top
