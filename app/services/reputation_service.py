from typing import Dict, List, Any
from datetime import datetime, timedelta
from app.core.smart_contract import SmartContract
from app.core.vector_db import VectorDB
from app.core.llm import LLM

class ReputationService:
    def __init__(self, smart_contract: SmartContract, vector_db: VectorDB, llm: LLM):
        self.smart_contract = smart_contract
        self.vector_db = vector_db
        self.llm = llm
        self.reputation_decay_rate = 0.99  # 1% decay per day
        self.contribution_weights = {
            "knowledge_addition": 10,
            "knowledge_update": 5,
            "proposal_creation": 15,
            "vote_cast": 2,
            "ethics_check": 5,
            "scenario_participation": 8
        }

    async def get_reputation(self, user_address: str) -> int:
        """
        Get the current reputation score for a user.
        
        Args:
            user_address (str): The Ethereum address of the user.
        
        Returns:
            int: The current reputation score.
        """
        return self.smart_contract.get_reputation(user_address)

    async def update_reputation(self, user_address: str, contribution_type: str, content: str) -> int:
        """
        Update a user's reputation based on a new contribution.
        
        Args:
            user_address (str): The Ethereum address of the user.
            contribution_type (str): The type of contribution made.
            content (str): The content of the contribution.
        
        Returns:
            int: The updated reputation score.
        """
        base_score = self.contribution_weights.get(contribution_type, 1)
        quality_score = await self._assess_contribution_quality(content, contribution_type)
        reputation_change = int(base_score * quality_score)
        
        current_reputation = await self.get_reputation(user_address)
        new_reputation = current_reputation + reputation_change
        
        # Update reputation on-chain
        tx_hash = self.smart_contract.update_reputation(user_address, reputation_change)
        
        # Record the contribution and reputation change
        self._record_contribution(user_address, contribution_type, content, reputation_change)
        
        return new_reputation

    async def decay_reputation(self, user_address: str) -> int:
        """
        Apply a decay to the user's reputation score to encourage continued participation.
        
        Args:
            user_address (str): The Ethereum address of the user.
        
        Returns:
            int: The updated reputation score after decay.
        """
        current_reputation = await self.get_reputation(user_address)
        days_since_last_activity = await self._days_since_last_activity(user_address)
        
        decayed_reputation = int(current_reputation * (self.reputation_decay_rate ** days_since_last_activity))
        reputation_change = decayed_reputation - current_reputation
        
        if reputation_change != 0:
            self.smart_contract.update_reputation(user_address, reputation_change)
        
        return decayed_reputation

    async def get_top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top contributors based on reputation scores.
        
        Args:
            limit (int): The number of top contributors to return.
        
        Returns:
            List[Dict[str, Any]]: A list of top contributors with their details.
        """
        # This would typically involve querying the blockchain or a database
        # For demonstration, we'll use a placeholder implementation
        top_contributors = self.smart_contract.get_top_contributors(limit)
        
        return [
            {
                "address": contributor["address"],
                "reputation": contributor["reputation"],
                "contributions": await self._get_user_contributions(contributor["address"])
            }
            for contributor in top_contributors
        ]

    async def process_community_feedback(self, contribution_id: str, feedback_score: int) -> None:
        """
        Process community feedback on a contribution and adjust reputation accordingly.
        
        Args:
            contribution_id (str): The ID of the contribution receiving feedback.
            feedback_score (int): The feedback score (-1 for negative, 0 for neutral, 1 for positive).
        """
        contribution = self._get_contribution(contribution_id)
        if not contribution:
            raise ValueError(f"Contribution with ID {contribution_id} not found.")
        
        reputation_change = feedback_score * 2  # Simple scaling, adjust as needed
        await self.update_reputation(contribution["user_address"], "community_feedback", str(feedback_score))

    async def _assess_contribution_quality(self, content: str, contribution_type: str) -> float:
        """
        Assess the quality of a contribution using the LLM.
        
        Args:
            content (str): The content of the contribution.
            contribution_type (str): The type of contribution.
        
        Returns:
            float: A quality score between 0 and 1.
        """
        prompt = f"Assess the quality of the following {contribution_type} on a scale of 0 to 1, where 1 is the highest quality:\n\n{content}\n\nQuality score:"
        response = self.llm.generate(prompt, max_length=10)
        try:
            return min(max(float(response.strip()), 0), 1)
        except ValueError:
            return 0.5  # Default to neutral if parsing fails

    def _record_contribution(self, user_address: str, contribution_type: str, content: str, reputation_change: int) -> None:
        """
        Record a user's contribution in the vector database.
        
        Args:
            user_address (str): The Ethereum address of the user.
            contribution_type (str): The type of contribution.
            content (str): The content of the contribution.
            reputation_change (int): The change in reputation from this contribution.
        """
        embedding = self.llm.embed(content)
        self.vector_db.add(
            embedding,
            content,
            {
                "user_address": user_address,
                "contribution_type": contribution_type,
                "reputation_change": reputation_change,
                "timestamp": datetime.now().isoformat()
            }
        )

    async def _days_since_last_activity(self, user_address: str) -> int:
        """
        Calculate the number of days since the user's last activity.
        
        Args:
            user_address (str): The Ethereum address of the user.
        
        Returns:
            int: The number of days since the last activity.
        """
        last_contribution = self.vector_db.search(
            query_vector=None,  # We're not doing a similarity search here
            filter={"user_address": user_address},
            limit=1,
            sort_by="timestamp",
            sort_order="desc"
        )
        
        if not last_contribution:
            return 0  # New user or no activity recorded
        
        last_activity_date = datetime.fromisoformat(last_contribution[0]['metadata']['timestamp'])
        days_since = (datetime.now() - last_activity_date).days
        return max(days_since, 0)  # Ensure non-negative

    async def _get_user_contributions(self, user_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the recent contributions of a user.
        
        Args:
            user_address (str): The Ethereum address of the user.
            limit (int): The maximum number of contributions to return.
        
        Returns:
            List[Dict[str, Any]]: A list of the user's recent contributions.
        """
        contributions = self.vector_db.search(
            query_vector=None,  # We're not doing a similarity search here
            filter={"user_address": user_address},
            limit=limit,
            sort_by="timestamp",
            sort_order="desc"
        )
        
        return [
            {
                "type": contribution['metadata']['contribution_type'],
                "content": contribution['content'][:100] + "...",  # Truncate for brevity
                "reputation_change": contribution['metadata']['reputation_change'],
                "timestamp": contribution['metadata']['timestamp']
            }
            for contribution in contributions
        ]

    def _get_contribution(self, contribution_id: str) -> Dict[str, Any]:
        """
        Get a specific contribution by its ID.
        
        Args:
            contribution_id (str): The ID of the contribution.
        
        Returns:
            Dict[str, Any]: The contribution details.
        """
        contribution = self.vector_db.get(contribution_id)
        if contribution:
            return {
                "user_address": contribution['metadata']['user_address'],
                "type": contribution['metadata']['contribution_type'],
                "content": contribution['content'],
                "reputation_change": contribution['metadata']['reputation_change'],
                "timestamp": contribution['metadata']['timestamp']
            }
        return None

    async def get_reputation_history(self, user_address: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get the reputation history of a user over a specified number of days.
        
        Args:
            user_address (str): The Ethereum address of the user.
            days (int): The number of days of history to retrieve.
        
        Returns:
            List[Dict[str, Any]]: A list of daily reputation scores.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # This would typically involve querying the blockchain or a database
        # For demonstration, we'll use a placeholder implementation
        history = self.smart_contract.get_reputation_history(user_address, start_date, end_date)
        
        return [
            {
                "date": entry["date"].isoformat(),
                "reputation": entry["reputation"]
            }
            for entry in history
        ]