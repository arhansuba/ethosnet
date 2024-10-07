from typing import Dict, Any
from web3 import Web3
from web3.contract import Contract
import json
from app.core.config import settings

class SmartContractService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_RPC_URL))
        self.contract_address = settings.ETHOSNET_CONTRACT_ADDRESS
        with open('app/contracts/EthosNet.json', 'r') as abi_file:
            contract_json = json.load(abi_file)
        self.contract_abi = contract_json['abi']
        self.contract: Contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)

    async def get_account_nonce(self, address: str) -> int:
        """Get the current nonce for the given address."""
        return self.w3.eth.get_transaction_count(address)

    async def send_transaction(self, function_name: str, *args, sender_address: str, private_key: str) -> Dict[str, Any]:
        """Send a transaction to the smart contract."""
        nonce = await self.get_account_nonce(sender_address)
        
        # Prepare the transaction
        txn = getattr(self.contract.functions, function_name)(*args).buildTransaction({
            'chainId': 1,  # Mainnet. Change as needed for other networks.
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign the transaction
        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
        
        # Send the transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for the transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {'tx_hash': tx_hash.hex(), 'status': tx_receipt['status']}

    async def call_function(self, function_name: str, *args) -> Any:
        """Call a read-only function on the smart contract."""
        return getattr(self.contract.functions, function_name)(*args).call()

    async def record_knowledge_contribution(self, author_id: str, entry_id: str, timestamp: int) -> Dict[str, Any]:
        """Record a knowledge contribution on the blockchain."""
        return await self.send_transaction('recordKnowledgeContribution', author_id, entry_id, timestamp,
                                           sender_address=settings.ETHOSNET_OPERATOR_ADDRESS,
                                           private_key=settings.ETHOSNET_OPERATOR_PRIVATE_KEY)

    async def record_knowledge_deletion(self, author_id: str, entry_id: str, timestamp: int) -> Dict[str, Any]:
        """Record a knowledge deletion on the blockchain."""
        return await self.send_transaction('recordKnowledgeDeletion', author_id, entry_id, timestamp,
                                           sender_address=settings.ETHOSNET_OPERATOR_ADDRESS,
                                           private_key=settings.ETHOSNET_OPERATOR_PRIVATE_KEY)

    async def update_reputation(self, user_id: str, new_reputation: float) -> Dict[str, Any]:
        """Update a user's reputation on the blockchain."""
        reputation_int = int(new_reputation * 100)  # Convert to integer (assume 2 decimal places)
        return await self.send_transaction('updateReputation', user_id, reputation_int,
                                           sender_address=settings.ETHOSNET_OPERATOR_ADDRESS,
                                           private_key=settings.ETHOSNET_OPERATOR_PRIVATE_KEY)

    async def get_reputation(self, user_id: str) -> float:
        """Get a user's reputation from the blockchain."""
        reputation_int = await self.call_function('getReputation', user_id)
        return reputation_int / 100  # Convert back to float

    async def record_ethics_evaluation(self, decision_id: str, score: int, timestamp: int) -> Dict[str, Any]:
        """Record an ethics evaluation on the blockchain."""
        return await self.send_transaction('recordEthicsEvaluation', decision_id, score, timestamp,
                                           sender_address=settings.ETHOSNET_OPERATOR_ADDRESS,
                                           private_key=settings.ETHOSNET_OPERATOR_PRIVATE_KEY)

    async def create_standard_proposal(self, proposed_standard: str) -> Dict[str, Any]:
        """Create a new ethical standard proposal on the blockchain."""
        return await self.send_transaction('createStandardProposal', proposed_standard,
                                           sender_address=settings.ETHOSNET_OPERATOR_ADDRESS,
                                           private_key=settings.ETHOSNET_OPERATOR_PRIVATE_KEY)

    async def vote_on_proposal(self, proposal_id: int, voter: str, vote: bool) -> Dict[str, Any]:
        """Record a vote on a proposal."""
        return await self.send_transaction('voteOnProposal', proposal_id, voter, vote,
                                           sender_address=settings.ETHOSNET_OPERATOR_ADDRESS,
                                           private_key=settings.ETHOSNET_OPERATOR_PRIVATE_KEY)

    async def get_proposal_status(self, proposal_id: int) -> Dict[str, Any]:
        """Get the status of a proposal."""
        return await self.call_function('getProposalStatus', proposal_id)

    async def get_proposal_vote_count(self, proposal_id: int) -> Dict[str, int]:
        """Get the vote count for a proposal."""
        votes = await self.call_function('getProposalVoteCount', proposal_id)
        return {'yes_votes': votes[0], 'no_votes': votes[1]}

    async def get_total_contributions(self, user_id: str) -> int:
        """Get the total number of contributions for a user."""
        return await self.call_function('getTotalContributions', user_id)

    async def get_user_activity(self, user_id: str) -> Dict[str, int]:
        """Get a summary of a user's activity."""
        activity = await self.call_function('getUserActivity', user_id)
        return {
            'contributions': activity[0],
            'evaluations': activity[1],
            'proposals': activity[2],
            'votes': activity[3]
        }