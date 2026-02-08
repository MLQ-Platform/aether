import os
from aether.config import get_config
from aether.logger import get_logger
from aether.pipeline.clause import generate_sub_clause
from aether.pipeline.clause import load_clause_graph
from aether.pipeline.thesis import generate_thesis
from aether.utils import save_json

logger = get_logger(__name__)


def main(
    clause_load_basedir: str = None,
    thesis_save_basedir: str = None,
    clause_version: str = "v0",
):
    config = get_config()
    db_dir = config.data.database_dir
    clause_load_basedir = clause_load_basedir or os.path.join(db_dir, "clause")
    thesis_save_basedir = thesis_save_basedir or os.path.join(db_dir, "thesis")

    clause_graph = load_clause_graph(clause_load_basedir, version=clause_version)
    subclause = generate_sub_clause(clause_graph)

    thesis = generate_thesis(*subclause.clause_trees.values(), config=config)
    logger.info(f"Thesis generated: {thesis.thesis[:100]}...")

    os.makedirs(thesis_save_basedir, exist_ok=True)
    savepath = os.path.join(thesis_save_basedir, f"thesis-{thesis.uuid}.json")
    save_json(thesis.model_dump(), savepath)
    return thesis


if __name__ == "__main__":
    main()
