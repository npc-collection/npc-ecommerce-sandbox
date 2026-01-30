"""AutoGen-based customer support agent for natural language interactions."""

from typing import Any, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_core.tools import FunctionTool

from config import get_settings, LLMFactory

settings = get_settings()

# Create the LLM model instance from settings
_llm_model = LLMFactory.from_settings(settings)


def get_model_client() -> Any:
    """Get the model client for the configured LLM provider.

    Returns:
        Model client compatible with AutoGen framework
    """
    return _llm_model.get_autogen_client()


# Tool functions for customer support
def lookup_order(order_number: str) -> str:
    """Look up an order by order number.

    Args:
        order_number: The order number to look up (e.g., ORD-12345678)

    Returns:
        Order details as a string
    """
    # Simulated order lookup - will be connected to database
    return f"""Order {order_number}:
- Status: Processing
- Items: 2 items
- Total: $149.99
- Estimated Delivery: 3-5 business days
- Shipping Address: 123 Main St, City, State 12345"""


def check_product_availability(product_sku: str) -> str:
    """Check if a product is available in stock.

    Args:
        product_sku: The product SKU to check

    Returns:
        Availability information
    """
    # Simulated availability check
    return f"Product {product_sku}: In Stock (45 units available). Ships within 24 hours."


def initiate_return(order_number: str, reason: str) -> str:
    """Initiate a return for an order.

    Args:
        order_number: The order number for the return
        reason: The reason for the return

    Returns:
        Return confirmation details
    """
    import uuid

    return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"
    return f"""Return initiated successfully:
- Return ID: {return_id}
- Order: {order_number}
- Reason: {reason}
- Instructions: Please ship the item within 14 days using the prepaid label sent to your email."""


def check_loyalty_points(customer_email: str) -> str:
    """Check customer loyalty points balance.

    Args:
        customer_email: The customer's email address

    Returns:
        Loyalty points information
    """
    # Simulated loyalty check
    return f"Loyalty account for {customer_email}: 2,450 points ($24.50 value). VIP Status: Gold"


def apply_discount_code(code: str, order_total: float) -> str:
    """Validate and apply a discount code.

    Args:
        code: The discount code to apply
        order_total: The current order total

    Returns:
        Discount application result
    """
    # Simulated discount validation
    discount_codes = {
        "SAVE10": 0.10,
        "SUMMER20": 0.20,
        "VIP15": 0.15,
    }

    if code.upper() in discount_codes:
        discount = discount_codes[code.upper()]
        savings = order_total * discount
        new_total = order_total - savings
        return f"Discount code {code} applied! You save ${savings:.2f}. New total: ${new_total:.2f}"
    return f"Sorry, the discount code '{code}' is not valid or has expired."


def escalate_to_human(issue_summary: str, customer_email: str) -> str:
    """Escalate an issue to a human support agent.

    Args:
        issue_summary: Summary of the customer's issue
        customer_email: Customer's email for follow-up

    Returns:
        Escalation confirmation
    """
    import uuid

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    return f"""Issue escalated to human support:
- Ticket ID: {ticket_id}
- Customer: {customer_email}
- Issue: {issue_summary}
- Expected Response: Within 2-4 hours during business hours
A support specialist will contact you shortly."""


# Create tool instances
order_lookup_tool = FunctionTool(lookup_order, description="Look up order details by order number")

availability_tool = FunctionTool(
    check_product_availability, description="Check if a product is available in stock"
)

return_tool = FunctionTool(initiate_return, description="Initiate a return for an order")

loyalty_tool = FunctionTool(
    check_loyalty_points, description="Check customer loyalty points balance"
)

discount_tool = FunctionTool(apply_discount_code, description="Validate and apply a discount code")

escalation_tool = FunctionTool(
    escalate_to_human, description="Escalate complex issues to human support"
)


def create_support_agent() -> AssistantAgent:
    """Create the main customer support agent."""
    model_client = get_model_client()

    return AssistantAgent(
        name="support_agent",
        model_client=model_client,
        tools=[
            order_lookup_tool,
            availability_tool,
            return_tool,
            loyalty_tool,
            discount_tool,
            escalation_tool,
        ],
        system_message="""You are a friendly and helpful customer support agent for an e-commerce store.

Your responsibilities:
1. Help customers with order inquiries (tracking, status, issues)
2. Answer product availability questions
3. Process returns and refunds
4. Apply discount codes and check loyalty points
5. Escalate complex issues to human agents when necessary

Guidelines:
- Always be polite, empathetic, and professional
- Use the available tools to look up real information
- Don't make up order details or product information - always use tools
- If you can't resolve an issue, offer to escalate to a human agent
- Thank customers for their patience and business
- Keep responses concise but complete

When a customer mentions an order number, always look it up first.
When ending a conversation successfully, say "RESOLVED" to indicate completion.""",
    )


def create_triage_agent() -> AssistantAgent:
    """Create an agent that triages customer requests."""
    model_client = get_model_client()

    return AssistantAgent(
        name="triage_agent",
        model_client=model_client,
        handoffs=["support_agent", "technical_agent"],
        system_message="""You are a customer service triage agent.

Your job is to understand the customer's request and route it appropriately:
- Order issues, returns, discounts, loyalty → hand off to support_agent
- Technical issues with the website or app → hand off to technical_agent
- General product questions → answer directly or hand off to support_agent

Be brief in your triage - quickly identify the issue type and hand off.""",
    )


def create_technical_agent() -> AssistantAgent:
    """Create an agent for technical support issues."""
    model_client = get_model_client()

    return AssistantAgent(
        name="technical_agent",
        model_client=model_client,
        system_message="""You are a technical support specialist for the e-commerce platform.

You help with:
- Website navigation issues
- Account login problems
- Payment processing errors
- Mobile app issues
- Browser compatibility

Provide clear, step-by-step troubleshooting instructions.
If you can't resolve the issue, recommend escalating to human support.
Say "RESOLVED" when the issue is fixed.""",
    )


async def create_support_team() -> SelectorGroupChat:
    """Create a multi-agent support team with intelligent routing."""
    model_client = get_model_client()

    support_agent = create_support_agent()
    triage_agent = create_triage_agent()
    technical_agent = create_technical_agent()

    termination = TextMentionTermination("RESOLVED") | MaxMessageTermination(15)

    team = SelectorGroupChat(
        [triage_agent, support_agent, technical_agent],
        model_client=model_client,
        termination_condition=termination,
    )

    return team


async def handle_customer_message(message: str, customer_email: Optional[str] = None) -> str:
    """Handle a customer support message.

    Args:
        message: The customer's message
        customer_email: Optional customer email for context

    Returns:
        The support agent's response
    """
    team = await create_support_team()

    context = f"Customer email: {customer_email}\n" if customer_email else ""
    full_message = f"{context}Customer message: {message}"

    result = await team.run(task=full_message)

    # Extract the final response
    if result.messages:
        # Get the last non-system message
        for msg in reversed(result.messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content

    return "I apologize, but I'm having trouble processing your request. Please try again or contact support@store.com."


async def run_simple_support(message: str) -> str:
    """Run a simple single-agent support interaction.

    Args:
        message: The customer's message

    Returns:
        The support agent's response
    """
    agent = create_support_agent()

    termination = TextMentionTermination("RESOLVED") | MaxMessageTermination(10)

    team = RoundRobinGroupChat(
        [agent],
        termination_condition=termination,
    )

    result = await team.run(task=message)

    if result.messages:
        for msg in reversed(result.messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content

    return "I apologize for the inconvenience. Please contact support@store.com for assistance."
