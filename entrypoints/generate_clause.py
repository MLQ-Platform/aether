import os
from aether.config import get_config
from aether.logger import get_logger
from aether.pipeline.clause import build_clause_graph

logger = get_logger(__name__)


def main(
    version: str = "v0",
    clause_save_basedir: str = None,
):
    config = get_config()
    clause_save_basedir = clause_save_basedir or os.path.join(
        config.data.database_dir, "clause"
    )

    clause_graph = build_clause_graph(config)

    os.makedirs(clause_save_basedir, exist_ok=True)
    savepath = os.path.join(clause_save_basedir, f"clause-{version}.json")
    clause_graph.save(savepath)
    logger.info(f"Clause graph saved to {savepath}")
    return clause_graph


if __name__ == "__main__":
    main()
