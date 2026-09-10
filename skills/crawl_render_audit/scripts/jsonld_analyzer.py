class JSONLDAnalyzer:
    """
    Deterministic JSON-LD analyzer.

    Reports structure and validity of JSON-LD blocks.
    It does not determine severity.
    """

    def analyze(self, data):
        data = data or []

        total_blocks = len(data)
        valid_blocks = 0
        invalid_blocks = 0
        types = []

        for block in data:
            if not isinstance(block, dict):
                invalid_blocks += 1
                continue

            if not block:
                invalid_blocks += 1
                continue

            valid_blocks += 1

            block_type = block.get("@type")

            if isinstance(block_type, list):
                types.extend(
                    item
                    for item in block_type
                    if isinstance(item, str)
                )
            elif isinstance(block_type, str):
                types.append(block_type)

        if total_blocks == 0:
            status = "missing"
        else:
            status = "present"

        return {
            "status": status,
            "evidence": {
                "total_blocks": total_blocks,
                "valid_blocks": valid_blocks,
                "invalid_blocks": invalid_blocks,
                "types": sorted(set(types)),
                "source": "raw_html",
                "confidence": "high",
            },
        }