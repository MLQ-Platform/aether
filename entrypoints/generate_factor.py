import os
from aether.agents.statement.schema import Statement
from aether.config import get_config
from aether.logger import get_logger
from aether.pipeline.factor import run_factor_revision
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def sample_statement(statement_load_basedir: str) -> Statement:
    files = [f for f in os.listdir(statement_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(statement_load_basedir, files[0])
    statement_graph = load_json(filepath)
    statement_str = list(statement_graph.values())[-1]["statement"]
    statement_uuid = list(statement_graph.values())[-1]["uuid"]
    statement = Statement(uuid=statement_uuid, statement=statement_str)
    return statement


def main(
    statement_load_basedir: str = None,
    factor_save_basedir: str = None,
):
    config = get_config()
    db_dir = config.data.database_dir
    statement_load_basedir = statement_load_basedir or os.path.join(db_dir, "statement")
    factor_save_basedir = factor_save_basedir or os.path.join(db_dir, "factor")

    statement = sample_statement(statement_load_basedir)
    factor_statement, factor_code = run_factor_revision(statement, config=config)
    factor_dict = {**factor_statement.model_dump(), **factor_code.model_dump()}

    os.makedirs(factor_save_basedir, exist_ok=True)
    savepath = os.path.join(factor_save_basedir, f"factor-{factor_statement.uuid}.json")
    save_json(factor_dict, savepath)
    logger.info(f"Factor saved to {savepath}")
    return factor_code


if __name__ == "__main__":
    main()
