from typing import Dict
from jsonrpc.db import get_mongo_db

def create_portfolio(address: str) -> Dict:
    """
    Create a portfolio by fetching all token balances from MongoDB for a specific address.
    
    Args:
        address: User's address (_id in MongoDB)
        
    Returns:
        Dict containing portfolio positions with token balances
    """
    try:
        # Get MongoDB connection from db module
        db = get_mongo_db()
        if not db:
            raise Exception("MongoDB connection not available")
            
        users_collection = db['users']
        
        # Initialize portfolio structure
        portfolio = {
            "positions": {}
        }
        
        # Find user and get all their tokens
        user = users_collection.find_one({"_id": address})
        if not user:
            raise Exception(f"User with address {address} not found")
            
        # Get all tokens for the user
        tokens = user.get('tokens', [])
        
        # Add each token to the portfolio
        for token in tokens:
            symbol = token.get('symbol')
            balance = token.get('balance', 0.0)
            
            if symbol:  # Only add if symbol exists
                portfolio["positions"][symbol] = {
                    "spot_quantity": balance,
                }
            
        return portfolio
        
    except Exception as e:
        print(f"Error fetching portfolio data: {e}")
        # Return empty portfolio in case of error
        return {
            "positions": {}
        }