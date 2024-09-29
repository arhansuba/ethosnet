import os
from typing import List, Dict, Any
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ABI for the EthosNet governance contract
ETHOSNET_ABI = [
    {
        "inputs": [{"name": "proposalId", "type": "uint256"}, {"name": "support", "type": "bool"}],
        "name": "castVote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "description", "type": "string"}],
        "name": "proposeStandard",
        "outputs": [{"name": "proposalId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "user", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "updateReputation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getReputation",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "proposalId", "type": "uint256"}],
        "name": "getProposal",
        "outputs": [{"name": "", "type": "tuple", "components": [
            {"name": "id", "type": "uint256"},
            {"name": "description", "type": "string"},
            {"name": "proposer", "type": "address"},
            {"name": "startBlock", "type": "uint256"},
            {"name": "endBlock", "type": "uint256"},
            {"name": "forVotes", "type": "uint256"},
            {"name": "againstVotes", "type": "uint256"},
            {"name": "executed", "type": "bool"}
        ]}],
        "stateMutability": "view",
        "type": "function"
    }
]

class SmartContract:
    def __init__(self, contract_name: str, contract_address: str):
        """
        Initialize the SmartContract class.
        
        Args:
            contract_name (str): Name of the contract (for logging purposes).
            contract_address (str): Ethereum address of the deployed contract.
        """
        self.contract_name = contract_name
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_NODE_URL')))
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=ETHOSNET_ABI)
        
        # Load the account from private key
        private_key = os.getenv('ETHEREUM_PRIVATE_KEY')
        self.account: LocalAccount = Account.from_key(private_key)
        
        print(f"Initialized {contract_name} contract at {contract_address}")

    def _send_transaction(self, function):
        """
        Helper method to send a transaction to the Ethereum network.
        
        Args:
            function: The contract function to call.
        
        Returns:
            str: The transaction hash.
        """
        transaction = function.build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        signed_txn = self.account.sign_transaction(transaction)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.transactionHash.hex()

    def propose_standard(self, description: str) -> str:
        """
        Propose a new ethical standard.
        
        Args:
            description (str): Description of the proposed standard.
        
        Returns:
            str: The ID of the newly created proposal.
        """
        function = self.contract.functions.proposeStandard(description)
        tx_hash = self._send_transaction(function)
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        proposal_id = self.contract.events.ProposalCreated().process_receipt(receipt)[0]['args']['proposalId']
        return str(proposal_id)

    def cast_vote(self, proposal_id: str, support: bool) -> str:
        """
        Cast a vote on a proposal.
        
        Args:
            proposal_id (str): The ID of the proposal to vote on.
            support (bool): True to vote in favor, False to vote against.
        
        Returns:
            str: The transaction hash of the vote transaction.
        """
        function = self.contract.functions.castVote(int(proposal_id), support)
        return self._send_transaction(function)

    def update_reputation(self, user: str, amount: int) -> str:
        """
        Update a user's reputation.
        
        Args:
            user (str): The Ethereum address of the user.
            amount (int): The amount to update the reputation by (can be positive or negative).
        
        Returns:
            str: The transaction hash of the reputation update transaction.
        """
        function = self.contract.functions.updateReputation(Web3.to_checksum_address(user), amount)
        return self._send_transaction(function)

    def get_reputation(self, user: str) -> int:
        """
        Get a user's current reputation.
        
        Args:
            user (str): The Ethereum address of the user.
        
        Returns:
            int: The user's current reputation score.
        """
        return self.contract.functions.getReputation(Web3.to_checksum_address(user)).call()

    def get_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Get details of a specific proposal.
        
        Args:
            proposal_id (str): The ID of the proposal.
        
        Returns:
            Dict[str, Any]: Details of the proposal.
        """
        proposal = self.contract.functions.getProposal(int(proposal_id)).call()
        return {
            "id": proposal[0],
            "description": proposal[1],
            "proposer": proposal[2],
            "startBlock": proposal[3],
            "endBlock": proposal[4],
            "forVotes": proposal[5],
            "againstVotes": proposal[6],
            "executed": proposal[7]
        }

    def record_decision(self, scenario: str, user_decision: str) -> str:
        """
        Record a user's decision in an ethics scenario.
        
        Args:
            scenario (str): A description of the ethics scenario.
            user_decision (str): The user's decision in the scenario.
        
        Returns:
            str: The transaction hash of the recorded decision.
        """
        # This could be implemented as a separate function in the smart contract
        # For now, we'll use the proposeStandard function as a placeholder
        description = f"Scenario: {scenario}\nDecision: {user_decision}"
        return self.propose_standard(description)

    def get_active_proposals(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active proposals.
        
        Returns:
            List[Dict[str, Any]]: A list of active proposals.
        """
        # This would typically involve querying events or a mapping in the smart contract
        # For demonstration, we'll return a placeholder implementation
        return [self.get_proposal("1"), self.get_proposal("2")]  # Placeholder IDs

    def execute_proposal(self, proposal_id: str) -> str:
        """
        Execute a passed proposal.
        
        Args:
            proposal_id (str): The ID of the proposal to execute.
        
        Returns:
            str: The transaction hash of the execution transaction.
        """
        # This would be implemented as a separate function in the smart contract
        # For now, we'll use a placeholder implementation
        function = self.contract.functions.executeProposal(int(proposal_id))
        return self._send_transaction(function)