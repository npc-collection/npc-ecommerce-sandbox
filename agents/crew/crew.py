"""CrewAI crew definition for e-commerce agents."""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from config import get_settings, LLMFactory
from .tools import inventory_tools, pricing_tools, order_tools

settings = get_settings()

# Create the LLM model instance from settings
_llm_model = LLMFactory.from_settings(settings)


def get_crewai_llm() -> Any:
    """Get the LLM instance for CrewAI agents.

    Returns:
        LLM instance compatible with CrewAI framework
    """
    return _llm_model.get_crewai_llm()


@CrewBase
class EcommerceCrew:
    """E-commerce multi-agent crew for inventory, pricing, and order management."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize the crew with configuration."""
        self.llm = get_crewai_llm()

    @agent
    def inventory_agent(self) -> Agent:
        """Create the inventory management agent."""
        return Agent(
            config=self.agents_config["inventory_agent"],
            tools=inventory_tools,
            llm=self.llm,
            verbose=settings.agent_verbose,
            max_iter=settings.agent_max_iter,
            max_rpm=settings.agent_max_rpm,
            memory=True,
        )

    @agent
    def pricing_agent(self) -> Agent:
        """Create the dynamic pricing agent."""
        return Agent(
            config=self.agents_config["pricing_agent"],
            tools=pricing_tools,
            llm=self.llm,
            verbose=settings.agent_verbose,
            max_iter=settings.agent_max_iter,
            max_rpm=settings.agent_max_rpm,
            memory=True,
        )

    @agent
    def order_agent(self) -> Agent:
        """Create the order fulfillment agent."""
        return Agent(
            config=self.agents_config["order_agent"],
            tools=order_tools,
            llm=self.llm,
            verbose=settings.agent_verbose,
            max_iter=settings.agent_max_iter,
            max_rpm=settings.agent_max_rpm,
            memory=True,
        )

    @task
    def check_inventory_levels_task(self) -> Task:
        """Task to check and analyze inventory levels."""
        return Task(
            config=self.tasks_config["check_inventory_levels"],
        )

    @task
    def analyze_pricing_opportunity_task(self) -> Task:
        """Task to analyze pricing opportunities."""
        return Task(
            config=self.tasks_config["analyze_pricing_opportunity"],
            context=[self.check_inventory_levels_task()],
        )

    @task
    def process_order_task(self) -> Task:
        """Task to process an incoming order."""
        return Task(
            config=self.tasks_config["process_order"],
        )

    @task
    def handle_low_stock_alert_task(self) -> Task:
        """Task to handle low stock alerts."""
        return Task(
            config=self.tasks_config["handle_low_stock_alert"],
        )

    @crew
    def inventory_pricing_crew(self) -> Crew:
        """Create crew for inventory and pricing optimization."""
        return Crew(
            agents=[self.inventory_agent(), self.pricing_agent()],
            tasks=[
                self.check_inventory_levels_task(),
                self.analyze_pricing_opportunity_task(),
            ],
            process=Process.sequential,
            verbose=settings.agent_verbose,
            memory=True,
        )

    @crew
    def order_processing_crew(self) -> Crew:
        """Create crew for order processing."""
        return Crew(
            agents=[self.order_agent(), self.inventory_agent()],
            tasks=[self.process_order_task()],
            process=Process.sequential,
            verbose=settings.agent_verbose,
            memory=True,
        )

    @crew
    def full_operations_crew(self) -> Crew:
        """Create full operations crew with all agents."""
        return Crew(
            agents=[
                self.inventory_agent(),
                self.pricing_agent(),
                self.order_agent(),
            ],
            tasks=[
                self.check_inventory_levels_task(),
                self.analyze_pricing_opportunity_task(),
                self.process_order_task(),
            ],
            process=Process.hierarchical,
            manager_llm=self.llm,
            verbose=settings.agent_verbose,
            memory=True,
        )


def run_inventory_check(inventory_data: dict) -> str:
    """Run inventory check task."""
    crew = EcommerceCrew()
    result = crew.inventory_pricing_crew().kickoff(
        inputs={"inventory_data": str(inventory_data), "sales_data": "{}"}
    )
    return result.raw


def run_order_processing(order_data: dict) -> str:
    """Run order processing task."""
    crew = EcommerceCrew()
    result = crew.order_processing_crew().kickoff(inputs={"order_data": str(order_data)})
    return result.raw
