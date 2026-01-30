"""Custom tools for CrewAI agents."""

from crewai.tools import BaseTool


class InventoryCheckTool(BaseTool):
    """Tool to check inventory levels for a product."""

    name: str = "check_inventory"
    description: str = (
        "Check current inventory level for a product by SKU. "
        "Returns quantity, reserved, and available stock."
    )

    def _run(self, sku: str) -> str:
        """Check inventory for a product."""
        # This will be connected to the actual database in production
        # For now, return simulated data
        return f"Inventory for {sku}: quantity=100, reserved=10, available=90, reorder_point=20"


class UpdateInventoryTool(BaseTool):
    """Tool to update inventory quantities."""

    name: str = "update_inventory"
    description: str = (
        "Update inventory quantity for a product. Use for receiving stock or adjustments."
    )

    def _run(self, sku: str, quantity_change: int, reason: str) -> str:
        """Update inventory quantity."""
        return f"Updated {sku} inventory by {quantity_change}. Reason: {reason}"


class GetProductPriceTool(BaseTool):
    """Tool to get current product pricing."""

    name: str = "get_product_price"
    description: str = (
        "Get current pricing information for a product "
        "including base price, current price, and cost."
    )

    def _run(self, sku: str) -> str:
        """Get product pricing."""
        return (
            f"Pricing for {sku}: base_price=$99.99, current_price=$89.99, cost=$50.00, margin=44%"
        )


class UpdatePriceTool(BaseTool):
    """Tool to update product price."""

    name: str = "update_price"
    description: str = (
        "Update the current price for a product. Requires SKU, new price, and reason for change."
    )

    def _run(self, sku: str, new_price: float, reason: str) -> str:
        """Update product price."""
        return f"Updated {sku} price to ${new_price:.2f}. Reason: {reason}"


class CreateOrderTool(BaseTool):
    """Tool to create a new order."""

    name: str = "create_order"
    description: str = "Create a new order with customer and item details."

    def _run(self, customer_id: int, items: str) -> str:
        """Create a new order."""
        import uuid

        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        return f"Created order {order_number} for customer {customer_id}. Items: {items}"


class UpdateOrderStatusTool(BaseTool):
    """Tool to update order status."""

    name: str = "update_order_status"
    description: str = (
        "Update the status of an existing order. "
        "Valid statuses: pending, confirmed, processing, shipped, delivered, cancelled"
    )

    def _run(self, order_number: str, new_status: str) -> str:
        """Update order status."""
        return f"Updated order {order_number} status to {new_status}"


class ReserveInventoryTool(BaseTool):
    """Tool to reserve inventory for an order."""

    name: str = "reserve_inventory"
    description: str = "Reserve inventory for a pending order. Prevents overselling."

    def _run(self, sku: str, quantity: int, order_number: str) -> str:
        """Reserve inventory for an order."""
        return f"Reserved {quantity} units of {sku} for order {order_number}"


class GetSalesDataTool(BaseTool):
    """Tool to get sales data for analysis."""

    name: str = "get_sales_data"
    description: str = (
        "Get recent sales data for a product or all products. Useful for demand analysis."
    )

    def _run(self, sku: str | None = None, days: int = 7) -> str:
        """Get sales data."""
        if sku:
            return (
                f"Sales data for {sku} (last {days} days): "
                "units_sold=45, revenue=$4,049.55, avg_daily=6.4"
            )
        return f"Total sales (last {days} days): orders=150, revenue=$15,000, avg_order_value=$100"


# Tool instances for use in agents
inventory_tools = [
    InventoryCheckTool(),
    UpdateInventoryTool(),
    ReserveInventoryTool(),
]

pricing_tools = [
    GetProductPriceTool(),
    UpdatePriceTool(),
    GetSalesDataTool(),
]

order_tools = [
    CreateOrderTool(),
    UpdateOrderStatusTool(),
    ReserveInventoryTool(),
    InventoryCheckTool(),
]
