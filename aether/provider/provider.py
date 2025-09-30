import os
from typing import Dict
from typing import NewType
from typing import Optional
import pandas as pd
import pyarrow.parquet as pq
from tqdm import tqdm

Ticker = NewType("Ticker", str)


class InMemoryDataProvider:
    """
    Parquet File by Ticker 로드 후 인메모리 저장
    """

    # store 클래스 변수: 모든 인스턴스들이 공통 참조
    _store: Dict[Ticker, pd.DataFrame] = {}

    def __init__(
        self,
        data_dir: Optional[str] = "data",
    ):
        self._data_dir = data_dir

        if not InMemoryDataProvider._store:
            self.load(data_dir)

    def load(self, data_dir: Optional[str] = None):
        """
        데이터 로드
        """
        if data_dir is None:
            data_dir = self._data_dir

        for f in tqdm(os.listdir(data_dir), desc="Loading dataframes ..."):
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

    def read_parquet(self, path: str) -> pd.DataFrame:
        """
        Read parquet file
        """
        table = pq.read_table(path, use_pandas_metadata=False)
        return table.to_pandas()
