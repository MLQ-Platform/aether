from aether import factory
from aether.agents.thesis.schema import Thesis
from aether.clause.tree.base import ClauseTree
from aether.config import Config
from aether.logger import get_logger
from aether.utils import generate_uuid

logger = get_logger(__name__)


def generate_thesis(
    tree_a: ClauseTree,
    tree_b: ClauseTree,
    config: Config = None,
) -> Thesis:
    thesis_agent = factory.get_thesis_agent(config)
    thesis = thesis_agent.run(tree_a, tree_b)
    thesis.uuid = generate_uuid()
    return thesis


async def generate_thesis_async(
    tree_a: ClauseTree,
    tree_b: ClauseTree,
    config: Config = None,
) -> Thesis:
    thesis_agent = factory.get_async_thesis_agent(config)
    thesis = await thesis_agent.run_async(tree_a, tree_b)
    thesis.uuid = generate_uuid()
    return thesis
