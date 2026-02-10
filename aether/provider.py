import os
from pathlib import Path
from typing import NewType
import pandas as pd
import pyarrow.parquet as pq

Ticker = NewType("Ticker", str)


class InMemoryDataProvider:
    """
    Parquet File by Ticker 로드 후 인메모리 저장
    """

    # store 클래스 변수: 모든 인스턴스들이 공통 참조
    _store: dict[Ticker, pd.DataFrame] = {}

    def __init__(
        self,
        data_dir: str | None = "data",
    ):

        module_dir = Path(__file__).resolve().parents[1]
        data_path = module_dir / data_dir

        self._data_dir = data_path

        if not InMemoryDataProvider._store:
            self.load(data_path)

    def load(self, data_dir: str | None = None):
        """
        데이터 로드
        """
        if data_dir is None:
            data_dir = self._data_dir

        for f in os.listdir(data_dir):
            # file 명 규칙: {ticker}.parquet
            ticker = Ticker(f.split(".")[0])
            # parquet를 데이터프레임으로 불러오기
            dataframe = self.read_parquet(os.path.join(data_dir, f))
            # store에 dateframe 삽입
            self.put(ticker, dataframe)

    def reset(self):
        """
        store 초기화
        """
        InMemoryDataProvider._store = {}

    def get(self, key: Ticker) -> pd.DataFrame:
        """
        티커 데이터 조회
        """
        return InMemoryDataProvider._store[key]

    def has(self, key: Ticker) -> bool:
        """
        티커 데이터 존재 여부 체크
        """
        return key in InMemoryDataProvider._store

    def put(self, key: Ticker, df: pd.DataFrame) -> None:
        """
        티커 데이터 저장
        """
        if key not in InMemoryDataProvider._store:
            InMemoryDataProvider._store[key] = df

    def get_tickers(self) -> list[Ticker]:
        """
        티커 리스트 조회
        """
        return list(InMemoryDataProvider._store.keys())

    def read_parquet(self, path: str) -> pd.DataFrame:
        """
        Read parquet file
        """
        table = pq.read_table(path, use_pandas_metadata=False)
        return table.to_pandas()
