from rapidfuzz import fuzz, process


class FieldMatcher:
    def __init__(
        self,
        aliases: dict[str, list[str]],
        fuzzy_threshold: float = 75.0,
        exclude: set[str] | None = None,
    ):
        self.aliases = aliases
        self.threshold = fuzzy_threshold
        self._exclude: set[str] = exclude or set()
        # Build reverse index: variant text → canonical field key
        self._index: dict[str, str] = {}
        for field_key, variants in aliases.items():
            self._index[field_key] = field_key
            for v in variants:
                self._index[v] = field_key

    def match(self, label: str) -> str | None:
        label = label.strip()
        if not label or label in self._exclude:
            return None

        # 1. Exact match
        if label in self._index:
            return self._index[label]

        # 2. Fuzzy match against all known variants
        choices = list(self._index.keys())
        result = process.extractOne(label, choices, scorer=fuzz.ratio)
        if result and result[1] >= self.threshold:
            return self._index[result[0]]

        return None

    def match_with_score(self, label: str) -> tuple[str | None, float]:
        label = label.strip()
        if not label or label in self._exclude:
            return None, 0.0

        if label in self._index:
            return self._index[label], 100.0

        choices = list(self._index.keys())
        result = process.extractOne(label, choices, scorer=fuzz.ratio)
        if result and result[1] >= self.threshold:
            return self._index[result[0]], result[1]

        return None, result[1] if result else 0.0
