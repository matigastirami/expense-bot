"""
OpenAI API usage tracking utilities.
Since OpenAI doesn't provide real-time credit balance via API, 
we'll track token usage instead and estimate costs.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# GPT-4o-mini pricing (as of 2024) - prices may change
GPT_4O_MINI_PRICING = {
    "input_tokens": 0.000150 / 1000,  # $0.15 per 1K input tokens
    "output_tokens": 0.000600 / 1000,  # $0.60 per 1K output tokens
}


def calculate_cost(usage: Dict[str, Any]) -> float:
    """
    Calculate the cost of an API call based on token usage.
    
    Args:
        usage: Usage dictionary from OpenAI/LangChain response
        
    Returns:
        Estimated cost in USD
    """
    if not usage:
        return 0.0
    
    # Handle both LangChain formats
    input_tokens = (
        usage.get("input_tokens", 0) or  # usage_metadata format
        usage.get("prompt_tokens", 0)    # response_metadata['token_usage'] format
    )
    output_tokens = (
        usage.get("output_tokens", 0) or  # usage_metadata format
        usage.get("completion_tokens", 0) # response_metadata['token_usage'] format
    )
    
    input_cost = input_tokens * GPT_4O_MINI_PRICING["input_tokens"]
    output_cost = output_tokens * GPT_4O_MINI_PRICING["output_tokens"]
    
    return input_cost + output_cost


def log_usage(usage: Optional[Dict[str, Any]], operation: str = "API call", message_preview: str = ""):
    """
    Log the token usage and estimated cost for an operation.
    
    Args:
        usage: Usage dictionary from OpenAI response
        operation: Description of the operation
        message_preview: Preview of the message being processed
    """
    if usage:
        # Handle both LangChain formats
        input_tokens = (
            usage.get("input_tokens", 0) or  # usage_metadata format
            usage.get("prompt_tokens", 0)    # response_metadata['token_usage'] format
        )
        output_tokens = (
            usage.get("output_tokens", 0) or  # usage_metadata format
            usage.get("completion_tokens", 0) # response_metadata['token_usage'] format
        )
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
        
        estimated_cost = calculate_cost(usage)
        
        log_message = (
            f"💰 {operation} - Tokens: In={input_tokens}, Out={output_tokens}, Total={total_tokens} | "
            f"Cost≈${estimated_cost:.6f}"
        )
        
        if message_preview:
            log_message += f" | Message: '{message_preview}'"
        
        logger.info(log_message)
        print(log_message)
    else:
        log_message = f"💰 {operation} - No usage data available"
        if message_preview:
            log_message += f" | Message: '{message_preview}'"
        
        logger.warning(log_message)
        print(log_message)


class UsageTracker:
    """Context manager for tracking OpenAI API token usage and costs."""
    
    def __init__(self, operation_name: str = "API operation", message_preview: str = ""):
        self.operation_name = operation_name
        self.message_preview = message_preview
        self.total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0, 
            "total_tokens": 0
        }
        self.call_count = 0
    
    def add_usage(self, usage: Optional[Dict[str, Any]]):
        """Add usage from an API response."""
        if usage:
            # Handle both LangChain formats
            input_tokens = (
                usage.get("input_tokens", 0) or  # usage_metadata format
                usage.get("prompt_tokens", 0)    # response_metadata['token_usage'] format
            )
            output_tokens = (
                usage.get("output_tokens", 0) or  # usage_metadata format
                usage.get("completion_tokens", 0) # response_metadata['token_usage'] format
            )
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            
            self.total_usage["prompt_tokens"] += input_tokens
            self.total_usage["completion_tokens"] += output_tokens
            self.total_usage["total_tokens"] += total_tokens
            self.call_count += 1
    
    async def __aenter__(self):
        """Initialize the tracker."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Log final usage summary."""
        total_cost = calculate_cost(self.total_usage)
        
        operation_desc = f"{self.operation_name} ({self.call_count} API calls)"
        
        log_message = (
            f"🎯 {operation_desc} TOTAL - "
            f"Tokens: In={self.total_usage['prompt_tokens']}, "
            f"Out={self.total_usage['completion_tokens']}, "
            f"Total={self.total_usage['total_tokens']} | "
            f"Cost≈${total_cost:.6f}"
        )
        
        if self.message_preview:
            log_message += f" | Message: '{self.message_preview}'"
        
        logger.info(log_message)
        print(log_message)
    
    @property
    def estimated_cost(self) -> float:
        """Get the estimated total cost."""
        return calculate_cost(self.total_usage)