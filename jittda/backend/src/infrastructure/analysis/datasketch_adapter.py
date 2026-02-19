"""
Datasketch Adapter — MinHash/LSH 기반 코드 유사도 탐지.

코드 청크 단위로 MinHash fingerprint를 생성하고,
LSH 인덱스로 유사 코드를 빠르게 탐지한다.
"""
from dataclasses import dataclass

from datasketch import MinHash, MinHashLSH


@dataclass(frozen=True)
class SimilarityResult:
    """코드 유사도 결과."""

    source_id: str
    target_id: str
    similarity: float  # 0.0 ~ 1.0


class DatasketchAdapter:
    """MinHash/LSH 기반 코드 유사도 탐지 어댑터."""

    def __init__(self, *, num_perm: int = 128, threshold: float = 0.5) -> None:
        """
        Args:
            num_perm: MinHash 순열 수 (정밀도 조절).
            threshold: LSH 유사도 임계값.
        """
        self._num_perm = num_perm
        self._threshold = threshold
        self._lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self._minhashes: dict[str, MinHash] = {}

    def create_minhash(self, code: str) -> MinHash:
        """코드 문자열에서 MinHash fingerprint를 생성한다.

        3-gram(shingle) 방식으로 토큰화한다.
        토큰이 3개 미만이면 개별 토큰을 사용한다.
        빈 문자열이면 빈 MinHash를 반환한다.
        """
        mh = MinHash(num_perm=self._num_perm)
        tokens = code.split()
        if len(tokens) >= 3:
            for i in range(len(tokens) - 2):
                shingle = " ".join(tokens[i : i + 3])
                mh.update(shingle.encode("utf-8"))
        else:
            for t in tokens:
                mh.update(t.encode("utf-8"))
        return mh

    def index_code(self, code_id: str, code: str) -> None:
        """코드 청크를 LSH 인덱스에 추가한다.

        이미 존재하는 키는 무시한다.
        """
        mh = self.create_minhash(code)
        self._minhashes[code_id] = mh
        try:
            self._lsh.insert(code_id, mh)
        except ValueError:
            # 이미 존재하는 키 — 무시
            pass

    def query_similar(self, code: str, *, top_k: int = 10) -> list[SimilarityResult]:
        """주어진 코드와 유사한 코드를 LSH에서 검색한다.

        반환값은 유사도 내림차순으로 정렬된다.
        """
        mh = self.create_minhash(code)
        candidates = self._lsh.query(mh)

        results: list[SimilarityResult] = []
        for candidate_id in candidates[:top_k]:
            candidate_mh = self._minhashes[candidate_id]
            sim = mh.jaccard(candidate_mh)
            results.append(
                SimilarityResult(
                    source_id="query",
                    target_id=candidate_id,
                    similarity=sim,
                )
            )
        return sorted(results, key=lambda r: r.similarity, reverse=True)

    def compute_pairwise_similarity(self, code_a: str, code_b: str) -> float:
        """두 코드 간 Jaccard 유사도를 직접 계산한다.

        Returns: 0.0 ~ 1.0
        """
        mh_a = self.create_minhash(code_a)
        mh_b = self.create_minhash(code_b)
        return mh_a.jaccard(mh_b)

    def compute_plagiarism_ratio(
        self,
        candidate_chunks: list[str],
        reference_chunks: list[str],
    ) -> float:
        """후보자 코드 청크 중 참조 코드와 유사한 비율을 계산한다.

        Args:
            candidate_chunks: 표절 여부를 검사할 코드 청크 목록.
            reference_chunks: 기준이 되는 참조 코드 청크 목록.

        Returns:
            0.0 ~ 1.0 범위의 표절 비율.
            candidate_chunks가 비어 있으면 0.0을 반환한다.
        """
        if not candidate_chunks:
            return 0.0

        # 참조 코드를 별도 LSH 인덱스에 추가 (인스턴스 인덱스와 분리)
        ref_lsh = MinHashLSH(threshold=self._threshold, num_perm=self._num_perm)
        for i, chunk in enumerate(reference_chunks):
            mh = self.create_minhash(chunk)
            ref_id = f"ref_{i}"
            try:
                ref_lsh.insert(ref_id, mh)
            except ValueError:
                pass

        plagiarized_count = 0
        for chunk in candidate_chunks:
            mh = self.create_minhash(chunk)
            if ref_lsh.query(mh):
                plagiarized_count += 1

        return plagiarized_count / len(candidate_chunks)
